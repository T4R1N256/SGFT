"""
Sales: confirm, cancel and adjust (WBS 3.3.5, 3.3.8). Owner: Jesús.

confirm_sale is the only write path of a sale (CLAUDE.md §5-bis): the New sale screen calls it online, and the
sync (pos/views_sync.py) calls it for every queued sale with its UUID and device timestamp. It follows the order of
the sync contract v1 §3.7, and every error that the sync must turn into a quarantine carries its reason in
`quarantine_reason`; the sale is never rejected offline (rule 9).

The order arrives with the pricing module's shape and keys (DEC-01), in integer cents:

    {"lineas": [{"platillo_id": 1, "precio_base_centavos": 8500, "cantidad": 2,
                 "modificadores": [{"tipo": "agregar", "insumo_id": 7, "ajuste_centavos": 1500}]}]}

A sale is immutable once charged (rule 7): cancel_sale and adjust_sale add a SaleAdjustment that points to it,
and the reason decides what is reverted (rule 11).

What the sync could not apply waits in QuarantinedOperation until an Administrator resolves it in Django Admin
with resolve_quarantine (rule 9, WBS 3.4.9); sales marked for review are closed with mark_sale_reviewed.
"""
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.catalog.models import Dish
from apps.inventory import services as inventory
from apps.pos.models import (
    AdjustmentKind, AdjustmentReason, CashRegisterSession, ModifierKind, Modifier, Order, OrderItem,
    OrderItemModifier, OperationType, PaymentMethod, QuarantinedOperation, QuarantineReason, QuarantineResolution,
    QuarantineStatus, ReviewReason, Sale, SaleAdjustment, SessionStatus,
)
from apps.pos import services_cash_session as cash
from apps.pos.services_cash_session import require_open_session
from apps.pos.services_pricing import calcular_total

# The contract sends "efectivo"/"transferencia"; the screen may send the model values.
PAYMENT_METHODS = {
    "efectivo": PaymentMethod.CASH, "transferencia": PaymentMethod.TRANSFER,
    PaymentMethod.CASH: PaymentMethod.CASH, PaymentMethod.TRANSFER: PaymentMethod.TRANSFER,
}
MODIFIER_KINDS = {"agregar": ModifierKind.ADD, "quitar": ModifierKind.REMOVE}
CENT = Decimal("0.01")


# ---------- Errores ----------
class SaleError(Exception):
    """Base of the errors of this module; the message is in Spanish, ready for the screen."""
    quarantine_reason = None  # set when the sync must keep the sale in quarantine instead


class UserWithoutPermissionError(SaleError):
    quarantine_reason = QuarantineReason.USER_WITHOUT_PERMISSION

    def __init__(self):
        super().__init__("Esta cuenta no puede registrar ventas.")


class InvalidSessionError(SaleError):
    quarantine_reason = QuarantineReason.INVALID_SESSION

    def __init__(self):
        super().__init__("El turno de caja de esta venta no existe o ya se cerró.")


class UnknownItemError(SaleError):
    quarantine_reason = QuarantineReason.UNKNOWN_DISH

    def __init__(self, detail):
        super().__init__(f"El pedido tiene platillos o modificadores que ya no existen: {detail}.")


class MissingRecipeError(SaleError):
    quarantine_reason = QuarantineReason.MISSING_RECIPE

    def __init__(self, dish_ids):
        self.dish_ids = dish_ids
        super().__init__(f"Hay platillos sin receta: {', '.join(map(str, dish_ids))}.")


class InconsistentTotalError(SaleError):
    quarantine_reason = QuarantineReason.INCONSISTENT_TOTAL

    def __init__(self, expected, charged):
        self.expected, self.charged = expected, charged
        super().__init__(f"El total cobrado ({charged} centavos) no corresponde al pedido ({expected} centavos).")


class InvalidOrderError(SaleError):
    """The order or the payment method is malformed. It is a bug of the client, not a quarantine case."""


class DuplicateSaleError(SaleError):
    """The UUID was already applied: the server discards the repeated sale (rule 8)."""

    def __init__(self, sale):
        self.sale = sale
        super().__init__("Esta venta ya se había registrado.")


class NotAdminError(SaleError):
    def __init__(self):
        super().__init__("Solo un Administrador puede cancelar o ajustar una venta.")


class AdjustmentError(SaleError):
    """A cancellation or adjustment that does not make sense for this sale."""


class ResolutionError(SaleError):
    """A quarantined operation that cannot be resolved that way; the message says what to do instead."""


# ---------- Confirmar ----------
def _cents_to_decimal(cents):
    return (Decimal(cents) / 100).quantize(CENT)


def _decimal_to_cents(amount):
    return int((amount * 100).to_integral_value())


def _parse_order(pedido):
    """
    Checks the order's shape with calcular_total and returns the total in cents and the parsed lines:
    [{"dish_id", "quantity", "base", "modifiers": [{"ingredient_id", "kind", "adjustment"}]}].
    """
    try:
        total = calcular_total(pedido)
    except ValueError as error:
        raise InvalidOrderError(str(error)) from None
    lines = []
    for linea in pedido["lineas"]:
        dish_id = linea.get("platillo_id")
        if type(dish_id) is not int:
            raise InvalidOrderError("Cada línea debe traer platillo_id.")
        modifiers = []
        for modificador in linea.get("modificadores", []):
            ingredient_id = modificador.get("insumo_id")
            if type(ingredient_id) is not int:
                raise InvalidOrderError("Cada modificador debe traer insumo_id.")
            modifiers.append({"ingredient_id": ingredient_id, "kind": MODIFIER_KINDS[modificador["tipo"]],
                              "adjustment": modificador.get("ajuste_centavos", 0)})
        lines.append({"dish_id": dish_id, "quantity": linea["cantidad"], "base": linea["precio_base_centavos"],
                      "modifiers": modifiers})
    if not lines:
        raise InvalidOrderError("El pedido no tiene líneas.")
    return total, lines


def _session_for_sale(session_uuid):
    """Online, the open session (rule 12). Offline, the session the device recorded, which must still be open."""
    if session_uuid is None:
        return require_open_session()
    session = CashRegisterSession.objects.filter(uuid=session_uuid).first()
    if session is None or session.status != SessionStatus.OPEN:
        raise InvalidSessionError()
    return session


def _catalog(lines):
    """The current dishes and modifier definitions the lines name; raises UnknownItemError if any is missing."""
    dishes = Dish.objects.in_bulk({line["dish_id"] for line in lines})
    missing = sorted({line["dish_id"] for line in lines} - set(dishes))
    if missing:
        raise UnknownItemError("platillos " + ", ".join(map(str, missing)))
    definitions = {
        (m.dish_id, m.ingredient_id, m.kind): m
        for m in Modifier.objects.filter(dish_id__in=dishes)
    }
    unknown = sorted({
        (line["dish_id"], m["ingredient_id"]) for line in lines for m in line["modifiers"]
        if (line["dish_id"], m["ingredient_id"], m["kind"]) not in definitions
    })
    if unknown:
        raise UnknownItemError("modificadores " + ", ".join(f"{i} en {d}" for d, i in unknown))
    return dishes, definitions


def _inventory_lines(lines, definitions):
    """The lines in the shape of inventory.deduct_for_sale; an extra uses its definition's quantity (rule 2)."""
    return [{
        "dish_id": line["dish_id"], "quantity": line["quantity"],
        "modifiers": [{"ingredient_id": m["ingredient_id"], "kind": m["kind"],
                       "quantity": definitions[(line["dish_id"], m["ingredient_id"], m["kind"])].quantity}
                      for m in line["modifiers"]],
    } for line in lines]


def _with_current_prices(lines, dishes, definitions):
    """The same lines with today's base prices and extras, in cents."""
    return [{**line, "base": _decimal_to_cents(dishes[line["dish_id"]].price), "modifiers": [
        {**m, "adjustment": _decimal_to_cents(
            definitions[(line["dish_id"], m["ingredient_id"], m["kind"])].price_adjustment)}
        for m in line["modifiers"]
    ]} for line in lines]


def _current_total(lines, dishes, definitions):
    """What the order costs with today's catalog, in cents (DEC-02 compares it with what was charged)."""
    return calcular_total({"lineas": [{
        "precio_base_centavos": _decimal_to_cents(dishes[line["dish_id"]].price),
        "cantidad": line["quantity"],
        "modificadores": [{
            "tipo": "agregar" if m["kind"] == ModifierKind.ADD else "quitar",
            "ajuste_centavos": _decimal_to_cents(
                definitions[(line["dish_id"], m["ingredient_id"], m["kind"])].price_adjustment),
        } for m in line["modifiers"]],
    } for line in lines]})


@transaction.atomic
def confirm_sale(user, pedido, payment_method, total_cobrado_centavos, *, uuid=None, session_uuid=None,
                 device_timestamp=None, deduct_inventory=True, current_prices=False):
    """
    Records a charged sale and deducts its inventory in the same transaction (rule 1). Returns the Sale.

    - user is who registered it: the device's cashier account, or the usuario_id of the queued operation.
    - Online, leave uuid, session_uuid and device_timestamp out: the sale goes to the open session.
    - Offline (sync), pass the operation's uuid, turno_uuid and marca_tiempo_dispositivo. A repeated uuid
      raises DuplicateSaleError with the sale already saved and changes nothing (rule 8).
    - deduct_inventory=False is the quarantine's "apply without deducting inventory" (rule 9).
    - current_prices=True is the quarantine's "apply with the current catalog": the lines take today's prices, so
      an order that did not match its own total can be recorded; what was charged is still what is recorded.

    Checks, in the contract's order: role, open session (before any pricing, rule 12), dishes and modifiers that
    exist, recipes, and that the charged total matches its own lines. What was charged is what is recorded
    (rule 14): if today's catalog gives another total, the sale is marked for review (precio_distinto), and so it
    is if an ingredient ends negative (existencia_negativa, rule 10).
    """
    if uuid is not None:
        existing = Sale.objects.filter(uuid=uuid).first()
        if existing is not None:
            raise DuplicateSaleError(existing)
    if not (user.is_active and (user.is_admin or user.is_cashier)):
        raise UserWithoutPermissionError()
    session = _session_for_sale(session_uuid)
    method = PAYMENT_METHODS.get(payment_method)
    if method is None:
        raise InvalidOrderError("El método de pago debe ser efectivo o transferencia.")
    if type(total_cobrado_centavos) is not int or total_cobrado_centavos < 0:
        raise InvalidOrderError("El total cobrado debe ser un entero de centavos.")
    expected, lines = _parse_order(pedido)
    dishes, definitions = _catalog(lines)
    if current_prices:
        lines = _with_current_prices(lines, dishes, definitions)
        expected = total_cobrado_centavos
    inventory_lines = _inventory_lines(lines, definitions)
    if deduct_inventory:
        try:
            inventory.required_quantities(inventory_lines)
        except inventory.MissingRecipeError as error:
            raise MissingRecipeError(error.dish_ids) from None
    if expected != total_cobrado_centavos:
        raise InconsistentTotalError(expected, total_cobrado_centavos)

    order = Order.objects.create(created_by=user)
    for line in lines:
        item = OrderItem.objects.create(order=order, dish=dishes[line["dish_id"]], quantity=line["quantity"],
                                        unit_price=_cents_to_decimal(line["base"]))
        OrderItemModifier.objects.bulk_create(
            OrderItemModifier(order_item=item, ingredient_id=m["ingredient_id"], kind=m["kind"],
                              price_adjustment=_cents_to_decimal(m["adjustment"] if m["kind"] == ModifierKind.ADD
                                                                 else 0))
            for m in line["modifiers"]
        )
    server_total = _current_total(lines, dishes, definitions)
    fields = dict(order=order, cash_session=session, created_by=user, payment_method=method,
                  charged_total=_cents_to_decimal(total_cobrado_centavos),
                  server_total=_cents_to_decimal(server_total),
                  device_timestamp=device_timestamp or timezone.now())
    if uuid is not None:
        fields["uuid"] = uuid
    try:
        with transaction.atomic():
            sale = Sale.objects.create(**fields)
    except IntegrityError:
        # The unique constraint is the real guarantee; another request saved the same UUID first.
        raise DuplicateSaleError(Sale.objects.get(uuid=uuid)) from None

    reasons = []
    if server_total != total_cobrado_centavos:
        reasons.append(ReviewReason.PRICE_DIFFERENT)
    if deduct_inventory and inventory.deduct_for_sale(sale.uuid, inventory_lines, user):
        reasons.append(ReviewReason.NEGATIVE_STOCK)
    if reasons:
        sale.needs_review = True
        sale.review_reasons = [str(reason) for reason in reasons]
        sale.save(update_fields=["needs_review", "review_reasons"])
    return sale


# ---------- Cancelar y ajustar ----------
def _require_admin(user):
    if not (user.is_active and user.is_admin):
        raise NotAdminError()


def _locked_sale(sale):
    """Locks the sale so two adjustments never revert the same units; refuses cancelled or closed-session sales."""
    sale = Sale.objects.select_for_update().select_related("cash_session").get(pk=sale.pk)
    if sale.adjustments.filter(kind=AdjustmentKind.CANCELLATION).exists():
        raise AdjustmentError("La venta ya está cancelada.")
    if sale.cash_session.status != SessionStatus.OPEN:
        raise AdjustmentError("La venta es de un turno que ya se cerró; su corte ya no se puede cambiar.")
    return sale


def _reverted_units(item):
    """Units of a line already reverted by error_captura or devolucion adjustments."""
    return sum(a.quantity for a in item.adjustments.all()
               if a.kind == AdjustmentKind.ADJUSTMENT and a.reason != AdjustmentReason.PAYMENT_CORRECTION)


def _unit_price(item):
    """What one unit of the line was charged: its base price plus its extras (the "quitar" ones cost 0)."""
    return item.unit_price + sum((m.price_adjustment for m in item.modifiers.all()), Decimal("0.00"))


def _item_inventory_line(item, units):
    """The units of a sold line in the shape of inventory.revert_sale_deduction."""
    definitions = {(m.ingredient_id, m.kind): m.quantity
                   for m in Modifier.objects.filter(dish_id=item.dish_id)}
    return {"dish_id": item.dish_id, "quantity": units, "modifiers": [
        {"ingredient_id": m.ingredient_id, "kind": m.kind,
         "quantity": definitions.get((m.ingredient_id, m.kind), Decimal("0"))}
        for m in item.modifiers.all()
    ]}


def _revert_inventory(sale, reason, lines, admin, note):
    """error_captura gives the ingredients back; devolucion records them as waste (rule 11)."""
    lines = [line for line in lines if line["quantity"]]
    if not lines or not inventory.sale_was_deducted(sale.uuid):
        return
    text = note or AdjustmentReason(reason).label
    if reason == AdjustmentReason.CAPTURE_ERROR:
        inventory.revert_sale_deduction(sale.uuid, lines, admin, text)
    else:
        inventory.record_sale_return(sale.uuid, lines, admin, text)


@transaction.atomic
def cancel_sale(admin, sale, reason, note=""):
    """
    Cancels the whole sale, minus what earlier adjustments already reverted. reason is error_captura (money and
    inventory back) or devolucion (money back, ingredients as waste). Only an active Administrator, the one who
    typed the PIN, authorizes it. Returns the SaleAdjustment.
    """
    _require_admin(admin)
    if reason not in (AdjustmentReason.CAPTURE_ERROR, AdjustmentReason.RETURN):
        raise AdjustmentError("Una cancelación es por error de captura o por devolución.")
    sale = _locked_sale(sale)
    reverted = sum((a.amount for a in sale.adjustments.all()), Decimal("0.00"))
    items = sale.order.items.prefetch_related("modifiers", "adjustments")
    lines = [_item_inventory_line(item, item.quantity - _reverted_units(item)) for item in items]
    _revert_inventory(sale, reason, lines, admin, note)
    return SaleAdjustment.objects.create(sale=sale, kind=AdjustmentKind.CANCELLATION, reason=reason,
                                         amount=sale.charged_total - reverted, note=note, authorized_by=admin)


@transaction.atomic
def adjust_sale(admin, sale, reason, *, order_item=None, quantity=None, new_payment_method=None, note=""):
    """
    Corrects part of a sale (rule 11). Returns the SaleAdjustment.

    - error_captura or devolucion: quantity units of order_item go back, with the same effects as a
      cancellation, limited to those units.
    - correccion_pago: reverts nothing; the cash close attributes the sale to new_payment_method.
    """
    _require_admin(admin)
    sale = _locked_sale(sale)
    if reason == AdjustmentReason.PAYMENT_CORRECTION:
        method = PAYMENT_METHODS.get(new_payment_method)
        if method is None:
            raise AdjustmentError("Indica el nuevo método de pago: efectivo o transferencia.")
        corrections = sale.adjustments.filter(reason=AdjustmentReason.PAYMENT_CORRECTION).order_by("created_at", "pk")
        current = corrections.last().new_payment_method if corrections else sale.payment_method
        if method == current:
            raise AdjustmentError("La venta ya está registrada con ese método de pago.")
        return SaleAdjustment.objects.create(sale=sale, kind=AdjustmentKind.ADJUSTMENT, reason=reason,
                                             new_payment_method=method, note=note, authorized_by=admin)
    if reason not in (AdjustmentReason.CAPTURE_ERROR, AdjustmentReason.RETURN):
        raise AdjustmentError("El motivo debe ser error de captura, devolución o corrección de pago.")
    if order_item is None or order_item.order_id != sale.order_id:
        raise AdjustmentError("Indica una línea de esta venta.")
    item = OrderItem.objects.prefetch_related("modifiers", "adjustments").get(pk=order_item.pk)
    remaining = item.quantity - _reverted_units(item)
    if remaining == 0:
        raise AdjustmentError("Esa línea ya se ajustó completa.")
    if type(quantity) is not int or not 1 <= quantity <= remaining:
        raise AdjustmentError(f"Se pueden ajustar de 1 a {remaining} unidades de esta línea.")
    _revert_inventory(sale, reason, [_item_inventory_line(item, quantity)], admin, note)
    return SaleAdjustment.objects.create(sale=sale, kind=AdjustmentKind.ADJUSTMENT, reason=reason,
                                         order_item=item, quantity=quantity, amount=_unit_price(item) * quantity,
                                         note=note, authorized_by=admin)


# ---------- Cuarentena y revisión ----------
def _quarantine_session(session_uuid):
    """
    The session a quarantined sale goes to: the one the device recorded if it is still open, or the current open
    session if the device's never reached the server (its opening was quarantined or discarded). A sale of a session
    that was already closed is refused: its cash close was saved and cannot change.
    """
    session = CashRegisterSession.objects.filter(uuid=session_uuid).first() if session_uuid else None
    if session is not None and session.status != SessionStatus.OPEN:
        raise ResolutionError("El turno de esta venta ya se cerró y su corte no se puede cambiar; descártala.")
    if session is None:
        session = cash.current_session()
        if session is None:
            raise ResolutionError("No hay un turno abierto: abre la caja para aplicar esta venta.")
    return session


def _registered_by(operation, admin, allowed):
    """Who the record is in the name of: who registered it on the device, or the Administrator that applies it."""
    user = operation.user
    return user if user is not None and user.is_active and allowed(user) else admin


def _apply_sale(operation, admin, deduct_inventory):
    payload = operation.payload
    session = _quarantine_session(payload.get("turno_uuid"))
    user = _registered_by(operation, admin, lambda u: u.is_admin or u.is_cashier)
    try:
        sale = confirm_sale(user, payload.get("pedido"), payload.get("metodo_pago"),
                            payload.get("total_cobrado_centavos"), uuid=operation.uuid, session_uuid=session.uuid,
                            device_timestamp=operation.device_timestamp, deduct_inventory=deduct_inventory,
                            current_prices=True)
    except DuplicateSaleError:
        raise ResolutionError("Ya hay una venta con este UUID: descártala como duplicada.") from None
    except MissingRecipeError as error:
        raise ResolutionError(f"{error} Agrega la receta o aplícala sin descontar inventario.") from None
    except UnknownItemError as error:
        raise ResolutionError(f"{error} No se puede aplicar con el catálogo actual; descártala.") from None
    except InvalidOrderError as error:
        raise ResolutionError(f"El contenido de la venta no es válido ({error}); descártala.") from None
    operation.sale = sale


def _apply_opening(operation, admin):
    payload = operation.payload
    cents = payload.get("efectivo_inicial_centavos")
    if type(cents) is not int or cents < 0:
        raise ResolutionError("La apertura no trae un efectivo inicial válido; descártala.")
    user = _registered_by(operation, admin, lambda u: u.is_admin)
    try:
        operation.cash_session = cash.open_session(user, _cents_to_decimal(cents), uuid=operation.uuid,
                                                   device_timestamp=operation.device_timestamp)
    except cash.DuplicateOperationError:
        raise ResolutionError("Ya hay un turno con este UUID: descártala como duplicada.") from None
    except (cash.SessionAlreadyOpenError, cash.DayAlreadyHasSessionError) as error:
        raise ResolutionError(f"{error} Descártala si era la misma apertura.") from None


@transaction.atomic
def resolve_quarantine(admin, operation, resolution):
    """
    Resolves a quarantined operation with one of the three outcomes of rule 9 and returns it:

    - apply: records it with the current catalog. A sale takes today's prices for its lines, keeps what was charged
      (marked precio_distinto if they differ) and deducts inventory; an opening opens the session.
    - apply_no_deduction: the same for a sale, without touching inventory (a dish without recipe, for instance).
    - discard: records nothing; for a real duplicate or a sale that cannot be recovered.

    Only an active Administrator resolves; the record keeps the device's UUID and time, and stays in the name of who
    registered it if that account can still do it, or else in the Administrator's. Raises ResolutionError, and
    changes nothing, when that outcome is not possible; the message says what to do instead.
    """
    if not (admin.is_active and admin.is_admin):
        raise ResolutionError("Solo un Administrador puede resolver la cuarentena.")
    operation = QuarantinedOperation.objects.select_for_update().get(pk=operation.pk)
    if operation.status != QuarantineStatus.PENDING:
        raise ResolutionError("Esta operación ya se resolvió.")
    resolution = QuarantineResolution(resolution)
    if resolution != QuarantineResolution.DISCARD:
        if operation.operation_type == OperationType.SALE:
            _apply_sale(operation, admin, deduct_inventory=resolution == QuarantineResolution.APPLY)
        elif resolution == QuarantineResolution.APPLY:
            _apply_opening(operation, admin)
        else:
            raise ResolutionError("Una apertura de turno no descuenta inventario: aplícala o descártala.")
    operation.status = QuarantineStatus.RESOLVED
    operation.resolution = resolution
    operation.resolved_by = admin
    operation.resolved_at = timezone.now()
    operation.save(update_fields=["status", "resolution", "resolved_by", "resolved_at", "sale", "cash_session"])
    return operation


def mark_sale_reviewed(admin, sale):
    """An Administrator checked a sale marked for review (rules 10 and 14); the sale itself does not change."""
    if not (admin.is_active and admin.is_admin):
        raise ResolutionError("Solo un Administrador puede revisar ventas.")
    updated = Sale.objects.filter(pk=sale.pk, needs_review=True, reviewed_at__isnull=True).update(
        reviewed_by=admin, reviewed_at=timezone.now())
    if not updated:
        raise ResolutionError("Esta venta no está pendiente de revisión.")
    sale.refresh_from_db()
    return sale
