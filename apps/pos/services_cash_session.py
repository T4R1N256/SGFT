"""
Cash register session: opening, closing and the open session (WBS 3.5.1). Owner: Jesús (pair: Tarín).

Rules 5, 12 and 13: one session per business day, only an Administrator opens or closes it, every sale needs an
open session, and the cash difference is recorded without blocking. The closing is refused while the device
still has unsynced sales. Offline the device opens the session and the server replays the opening through
open_session with the operation's UUID and device timestamp, revalidating the role (the sync turns these
exceptions into quarantine reasons).
"""
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.pos.models import AdjustmentReason, CashRegisterSession, PaymentMethod, Sale, SessionStatus


class CashSessionError(Exception):
    """Base of the errors of this module; the message is in Spanish, ready for the screen."""


class NotAdminError(CashSessionError):
    def __init__(self):
        super().__init__("Solo un Administrador puede abrir o cerrar la caja.")


class SessionAlreadyOpenError(CashSessionError):
    def __init__(self):
        super().__init__("Ya hay un turno de caja abierto.")


class DayAlreadyHasSessionError(CashSessionError):
    def __init__(self, business_date):
        self.business_date = business_date
        super().__init__(f"Ya hubo un turno de caja el {business_date:%d/%m/%Y}: solo hay uno por jornada.")


class DuplicateOperationError(CashSessionError):
    """The UUID of the opening was already applied: the server discards the repeated operation (rule 8)."""

    def __init__(self, session):
        self.session = session
        super().__init__("Esta apertura ya se había registrado.")


class NoOpenSessionError(CashSessionError):
    def __init__(self):
        super().__init__("No hay un turno de caja abierto. Pide al Administrador que abra la caja.")


class PendingSalesError(CashSessionError):
    def __init__(self, pending):
        self.pending = pending
        venta = "venta" if pending == 1 else "ventas"
        super().__init__(f"No se puede cerrar la caja: faltan {pending} {venta} por sincronizar.")


class InvalidAmountError(CashSessionError):
    def __init__(self, field):
        super().__init__(f"{field} debe ser una cantidad de 0 o más, con a lo más 2 decimales.")


def _amount(value, field):
    try:
        value = Decimal(value)
    except (ArithmeticError, TypeError, ValueError):
        raise InvalidAmountError(field) from None
    if not value.is_finite() or value < 0 or value != value.quantize(Decimal("0.01")):
        raise InvalidAmountError(field)
    return value


def _require_admin(user):
    if not (user.is_active and user.is_admin):
        raise NotAdminError()


def current_session():
    """The open session, or None."""
    return CashRegisterSession.objects.filter(status=SessionStatus.OPEN).first()


def require_open_session():
    """The open session; raises NoOpenSessionError if there is none (rule 12, checked before pricing a sale)."""
    session = current_session()
    if session is None:
        raise NoOpenSessionError()
    return session


@transaction.atomic
def open_session(admin, opening_amount, *, uuid=None, device_timestamp=None, business_date=None):
    """
    Opens the day's session with opening_amount in the drawer. admin must be an active Administrator (the one
    who typed the PIN): the session is recorded in their name. An offline opening passes its uuid and
    device_timestamp; a repeated uuid raises DuplicateOperationError with the session already saved.
    """
    if uuid is not None:
        existing = CashRegisterSession.objects.filter(uuid=uuid).first()
        if existing is not None:
            raise DuplicateOperationError(existing)
    _require_admin(admin)
    opening_amount = _amount(opening_amount, "El efectivo inicial")
    now = timezone.now()
    device_timestamp = device_timestamp or now
    business_date = business_date or timezone.localdate(device_timestamp)
    if CashRegisterSession.objects.filter(status=SessionStatus.OPEN).exists():
        raise SessionAlreadyOpenError()
    if CashRegisterSession.objects.filter(business_date=business_date).exists():
        raise DayAlreadyHasSessionError(business_date)
    fields = dict(business_date=business_date, opened_by=admin, opening_amount=opening_amount,
                  device_timestamp=device_timestamp)
    if uuid is not None:
        fields["uuid"] = uuid
    try:
        with transaction.atomic():
            return CashRegisterSession.objects.create(**fields)
    except IntegrityError:
        # The unique constraints are the real guarantee; another request won the race.
        if uuid is not None and CashRegisterSession.objects.filter(uuid=uuid).exists():
            raise DuplicateOperationError(CashRegisterSession.objects.get(uuid=uuid)) from None
        raise SessionAlreadyOpenError() from None


def _effective_method(sale):
    """The method the cash close attributes the sale to: the last correccion_pago wins (rule 11)."""
    corrections = [a for a in sale.adjustments.all() if a.reason == AdjustmentReason.PAYMENT_CORRECTION]
    if corrections:
        return max(corrections, key=lambda a: (a.created_at, a.pk)).new_payment_method
    return sale.payment_method


def sales_totals(session):
    """
    {"cash": Decimal, "transfer": Decimal}: what the session's sales charged by payment method, minus the money
    reverted by cancellations and adjustments (rule 11). Computed from what was recorded (rule 5).
    """
    totals = {PaymentMethod.CASH: Decimal("0.00"), PaymentMethod.TRANSFER: Decimal("0.00")}
    sales = Sale.objects.filter(cash_session=session).prefetch_related("adjustments")
    for sale in sales:
        reverted = sum((a.amount for a in sale.adjustments.all()), Decimal("0.00"))
        totals[_effective_method(sale)] += sale.charged_total - reverted
    return {str(method): total for method, total in totals.items()}


def expected_cash(session):
    """Cash that should be in the drawer: the opening amount plus the cash sales, net of reversions."""
    return session.opening_amount + sales_totals(session)[PaymentMethod.CASH]


@transaction.atomic
def close_session(admin, closing_amount, *, pending_sales=0):
    """
    Closes the open session with the cash counted in the drawer. pending_sales is how many sales the device
    has not synced yet: if there are any, the close is refused (rule 5). The difference against the expected
    cash is stored as information and never blocks (rule 13). Returns the closed session.
    """
    _require_admin(admin)
    if pending_sales:
        raise PendingSalesError(pending_sales)
    closing_amount = _amount(closing_amount, "El efectivo al cierre")
    session = CashRegisterSession.objects.select_for_update().filter(status=SessionStatus.OPEN).first()
    if session is None:
        raise NoOpenSessionError()
    session.expected_amount = expected_cash(session)
    session.closing_amount = closing_amount
    session.cash_difference = closing_amount - session.expected_amount
    session.closed_by = admin
    session.status = SessionStatus.CLOSED
    session.save(update_fields=["expected_amount", "closing_amount", "cash_difference", "closed_by", "status"])
    return session
