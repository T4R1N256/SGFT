"""
POST /pos/sync/: applies the device's offline queue (WBS 3.4.6), contract v1
(docs/decisiones/contrato-sync-pdv.md). Owner: Jared (pair: Jesús).

The view only translates: every operation goes through the same services as online (open_session, confirm_sale),
so there is a single write path. What the server cannot apply goes to QuarantinedOperation and is never rejected
(rule 9); a repeated UUID answers «duplicada» (rule 8). Each operation runs in its own transaction, so one failure
never reverts the rest of the batch.
"""
import json
from decimal import Decimal
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from apps.pos import services as sales
from apps.pos import services_cash_session as cash
from apps.pos.models import CashRegisterSession, OperationType, QuarantinedOperation, QuarantineReason, Sale

CONTRACT_VERSION = 1
MAX_OPERATIONS = 100
OPENING, SALE = OperationType.SESSION_OPENING.value, OperationType.SALE.value

APPLIED, APPLIED_WITH_REVIEW, DUPLICATE, QUARANTINE = "aplicada", "aplicada_con_revision", "duplicada", "cuarentena"

# Errors of the opening that the contract sends to quarantine (§3.5 and §3.6).
OPENING_QUARANTINE = {
    cash.NotAdminError: QuarantineReason.USER_WITHOUT_PERMISSION,
    cash.SessionAlreadyOpenError: QuarantineReason.SESSION_ALREADY_OPEN,
    cash.DayAlreadyHasSessionError: QuarantineReason.SESSION_ALREADY_OPEN,
}


class BadBatch(Exception):
    """The whole batch is refused (400) and nothing is applied: the client keeps its queue."""


def _error(message, status):
    return JsonResponse({"version_contrato": CONTRACT_VERSION, "detalle": message}, status=status)


def _int(value, minimum=0):
    return type(value) is int and value >= minimum


def _parse(operation):
    """Checks one operation's envelope; returns (uuid, device timestamp). Raises BadBatch if it is malformed."""
    if not isinstance(operation, dict):
        raise BadBatch("Cada operación debe ser un objeto.")
    try:
        uuid = UUID(str(operation.get("uuid")))
    except ValueError:
        raise BadBatch("Una operación no trae un uuid válido.") from None
    when = parse_datetime(str(operation.get("marca_tiempo_dispositivo") or ""))
    if when is None or when.tzinfo is None:
        raise BadBatch(f"{uuid}: marca_tiempo_dispositivo debe ser ISO 8601 con zona horaria.")
    if not _int(operation.get("usuario_id"), 1):
        raise BadBatch(f"{uuid}: usuario_id debe ser un entero.")
    kind = operation.get("tipo")
    if kind == OPENING:
        if not _int(operation.get("efectivo_inicial_centavos")):
            raise BadBatch(f"{uuid}: efectivo_inicial_centavos debe ser un entero de 0 o más.")
    elif kind == SALE:
        try:
            UUID(str(operation.get("turno_uuid")))
        except ValueError:
            raise BadBatch(f"{uuid}: turno_uuid no es un UUID.") from None
    else:
        raise BadBatch(f"{uuid}: tipo debe ser «apertura_turno» o «venta».")
    return uuid, when


def _already_known(uuid):
    """The UUID is unique across the three tables (rule 8)."""
    return (Sale.objects.filter(uuid=uuid).exists() or CashRegisterSession.objects.filter(uuid=uuid).exists()
            or QuarantinedOperation.objects.filter(uuid=uuid).exists())


def _quarantine(operation, uuid, when, user, reason):
    QuarantinedOperation.objects.create(uuid=uuid, operation_type=operation["tipo"], payload=operation,
                                        reason=reason, user=user, device_timestamp=when)
    return {"uuid": str(uuid), "estado": QUARANTINE, "motivo": str(reason)}


def _apply_opening(operation, uuid, when, user):
    if user is None:
        return _quarantine(operation, uuid, when, None, QuarantineReason.USER_WITHOUT_PERMISSION)
    amount = Decimal(operation["efectivo_inicial_centavos"]) / 100
    try:
        cash.open_session(user, amount, uuid=uuid, device_timestamp=when)
    except cash.DuplicateOperationError:
        return {"uuid": str(uuid), "estado": DUPLICATE}
    except tuple(OPENING_QUARANTINE) as error:
        return _quarantine(operation, uuid, when, user, OPENING_QUARANTINE[type(error)])
    return {"uuid": str(uuid), "estado": APPLIED}


def _apply_sale(operation, uuid, when, user):
    if user is None:
        return _quarantine(operation, uuid, when, None, QuarantineReason.USER_WITHOUT_PERMISSION)
    try:
        sale = sales.confirm_sale(user, operation.get("pedido"), operation.get("metodo_pago"),
                                  operation.get("total_cobrado_centavos"), uuid=uuid,
                                  session_uuid=UUID(str(operation["turno_uuid"])), device_timestamp=when)
    except sales.DuplicateSaleError:
        return {"uuid": str(uuid), "estado": DUPLICATE}
    except sales.InvalidOrderError:
        # An order that is not even well formed does not match its own total: parity error or altered data.
        return _quarantine(operation, uuid, when, user, QuarantineReason.INCONSISTENT_TOTAL)
    except sales.SaleError as error:
        if error.quarantine_reason is None:
            raise
        return _quarantine(operation, uuid, when, user, error.quarantine_reason)
    if sale.needs_review:
        return {"uuid": str(uuid), "estado": APPLIED_WITH_REVIEW, "motivos": list(sale.review_reasons)}
    return {"uuid": str(uuid), "estado": APPLIED}


def _apply(operation, uuid, when):
    if _already_known(uuid):
        return {"uuid": str(uuid), "estado": DUPLICATE}
    user = get_user_model().objects.filter(pk=operation["usuario_id"]).first()
    apply = _apply_opening if operation["tipo"] == OPENING else _apply_sale
    try:
        with transaction.atomic():
            return apply(operation, uuid, when, user)
    except IntegrityError:
        # Another request saved the same UUID first; the unique constraints are the real guarantee.
        if _already_known(uuid):
            return {"uuid": str(uuid), "estado": DUPLICATE}
        raise


@require_POST
def sync_operations(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.4.6
    URL name    : pos:sync_operations      Método: POST (JSON, encabezado X-CSRFToken)
    Roles       : cualquier sesión activa; el rol se revalida por operación con usuario_id (DEC-05)
    Plantilla   : ninguna; responde JSON
    Respuestas  : 200 {version_contrato, resultados: [{uuid, estado, motivo | motivos}]} en el orden recibido
                  401 sin sesión · 403 CSRF · 400 lote mal formado o versión desconocida · 413 más de 100
                  operaciones. Fuera del 200 no se aplica nada y el cliente conserva su cola.
    Orden       : primero las aperturas, luego las ventas, cada grupo por marca_tiempo_dispositivo (§3.2)
    """
    if not request.user.is_authenticated:
        return _error("Activa el dispositivo para sincronizar.", 401)
    try:
        batch = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return _error("El lote no es JSON válido.", 400)
    if not isinstance(batch, dict) or not isinstance(batch.get("operaciones"), list):
        return _error("El lote debe traer la lista «operaciones».", 400)
    if batch.get("version_contrato") != CONTRACT_VERSION:
        return _error(f"Versión de contrato desconocida; el servidor usa la {CONTRACT_VERSION}.", 400)
    operations = batch["operaciones"]
    if len(operations) > MAX_OPERATIONS:
        return _error(f"Máximo {MAX_OPERATIONS} operaciones por envío.", 413)
    try:
        parsed = [(operation, *_parse(operation)) for operation in operations]
    except BadBatch as error:
        return _error(str(error), 400)

    # A UUID repeated inside the batch is applied once; its second appearance answers «duplicada».
    results = [None] * len(parsed)
    order = sorted(range(len(parsed)), key=lambda i: (parsed[i][0]["tipo"] != OPENING, parsed[i][2]))
    for index in order:
        results[index] = _apply(*parsed[index])
    return JsonResponse({"version_contrato": CONTRACT_VERSION, "resultados": results})
