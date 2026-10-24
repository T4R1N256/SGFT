"""
Order, OrderItem, Modifier, Sale, SaleAdjustment, CashRegisterSession and QuarantinedOperation, the generic
quarantine for every synced operation that could not be applied (WBS 3.3.x, 3.4.x, 3.5.x). Owner: Jesús, who reviews every change; whoever writes a model generates its migration after telling him (DEC-37).
"""

from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

User = settings.AUTH_USER_MODEL


# ---------- Opciones ----------
class SessionStatus(models.TextChoices):
    OPEN = "open", "Abierto"
    CLOSED = "closed", "Cerrado"


class ModifierKind(models.TextChoices):
    ADD = "add", "Agregar"
    REMOVE = "remove", "Quitar"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Efectivo"
    TRANSFER = "transfer", "Transferencia"


class ReviewReason(models.TextChoices):
    PRICE_DIFFERENT = "precio_distinto", "Precio distinto"
    NEGATIVE_STOCK = "existencia_negativa", "Existencia negativa"


class QuarantineReason(models.TextChoices):
    USER_WITHOUT_PERMISSION = "usuario_sin_permiso", "Usuario sin permiso"
    SESSION_ALREADY_OPEN = "turno_ya_abierto", "Turno ya abierto"
    INVALID_SESSION = "turno_invalido", "Turno inválido"
    UNKNOWN_DISH = "platillo_desconocido", "Platillo desconocido"
    MISSING_RECIPE = "receta_faltante", "Receta faltante"
    INCONSISTENT_TOTAL = "total_inconsistente", "Total inconsistente"


class OperationType(models.TextChoices):
    SESSION_OPENING = "apertura_turno", "Apertura de turno"
    SALE = "venta", "Venta"


class QuarantineStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    RESOLVED = "resolved", "Resuelta"


class QuarantineResolution(models.TextChoices):
    APPLY = "apply", "Aplicar"
    APPLY_NO_DEDUCTION = "apply_no_deduction", "Aplicar sin descontar inventario"
    DISCARD = "discard", "Descartar"


def validate_review_reasons(value):
    """review_reasons es una lista JSON; cada elemento debe ser un motivo válido."""
    if not isinstance(value, list):
        raise ValidationError("Debe ser una lista de motivos.")
    invalid = [reason for reason in value if reason not in ReviewReason.values]
    if invalid:
        raise ValidationError(
            "Motivos no válidos: %(invalid)s", params={"invalid": ", ".join(map(str, invalid))}
        )


# ---------- Turno de caja ----------
class CashRegisterSession(models.Model):
    uuid = models.UUIDField("UUID", default=uuid4, unique=True, editable=False)
    business_date = models.DateField("fecha de negocio")
    opened_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="opened_cash_sessions", verbose_name="abierto por"
    )
    closed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="closed_cash_sessions",
        null=True, blank=True, verbose_name="cerrado por",
    )
    opening_amount = models.DecimalField("efectivo inicial", max_digits=10, decimal_places=2)
    closing_amount = models.DecimalField(
        "efectivo al cierre", max_digits=10, decimal_places=2, null=True, blank=True
    )
    expected_amount = models.DecimalField(
        "efectivo esperado", max_digits=10, decimal_places=2, null=True, blank=True
    )
    cash_difference = models.DecimalField(
        "diferencia de caja", max_digits=10, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        "estado", max_length=10, choices=SessionStatus.choices, default=SessionStatus.OPEN
    )
    device_timestamp = models.DateTimeField("hora del dispositivo")
    server_timestamp = models.DateTimeField("hora del servidor", auto_now_add=True)

    class Meta:
        db_table = "cash_register_sessions"
        verbose_name = "turno de caja"
        verbose_name_plural = "turnos de caja"
        constraints = [
            models.UniqueConstraint(fields=["business_date"], name="pos_session_one_per_day"),
            models.UniqueConstraint(
                fields=["status"],
                condition=Q(status="open"),
                name="pos_session_single_open",
            ),
        ]

    def __str__(self):
        return f"Turno {self.business_date} ({self.get_status_display()})"


# ---------- Pedido y líneas ----------
class Order(models.Model):
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="orders", verbose_name="creado por"
    )
    created_at = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        db_table = "orders"
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self):
        return f"Pedido {self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name="items", verbose_name="pedido"
    )
    dish = models.ForeignKey("catalog.Dish", on_delete=models.PROTECT, verbose_name="platillo")
    quantity = models.PositiveIntegerField("cantidad")
    unit_price = models.DecimalField("precio unitario", max_digits=10, decimal_places=2)

    class Meta:
        db_table = "order_items"
        verbose_name = "línea de pedido"
        verbose_name_plural = "líneas de pedido"
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="pos_orderitem_quantity_gt_0"),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.dish_id}"


# ---------- Modificadores ----------
class Modifier(models.Model):
    """Extras y 'quitar ingrediente' disponibles para cada platillo."""
    dish = models.ForeignKey("catalog.Dish", on_delete=models.PROTECT, verbose_name="platillo")
    ingredient = models.ForeignKey(
        "catalog.Ingredient", on_delete=models.PROTECT, verbose_name="insumo"
    )
    kind = models.CharField("tipo", max_length=10, choices=ModifierKind.choices)
    price_adjustment = models.DecimalField(
        "ajuste de precio", max_digits=10, decimal_places=2, default=0
    )
    quantity = models.DecimalField(
        "cantidad de insumo", max_digits=10, decimal_places=3, default=0,
        help_text="Cuánto insumo descuenta un extra.",
    )

    class Meta:
        db_table = "modifiers"
        verbose_name = "modificador"
        verbose_name_plural = "modificadores"
        constraints = [
            models.UniqueConstraint(
                fields=["dish", "ingredient", "kind"], name="pos_modifier_unique_combo"
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} {self.ingredient_id} en {self.dish_id}"


class OrderItemModifier(models.Model):
    """Copia de lo cobrado: la venta no cambia si después cambia el catálogo."""
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.PROTECT, related_name="modifiers", verbose_name="línea"
    )
    ingredient = models.ForeignKey(
        "catalog.Ingredient", on_delete=models.PROTECT, verbose_name="insumo"
    )
    kind = models.CharField("tipo", max_length=10, choices=ModifierKind.choices)
    price_adjustment = models.DecimalField(
        "ajuste de precio", max_digits=10, decimal_places=2, default=0
    )

    class Meta:
        db_table = "order_item_modifiers"
        verbose_name = "modificador de línea"
        verbose_name_plural = "modificadores de línea"

    def __str__(self):
        return f"{self.get_kind_display()} {self.ingredient_id}"


# ---------- Venta ----------
class Sale(models.Model):
    """Inmutable desde el cobro. Las cancelaciones irán en SaleAdjustment, no aquí."""
    uuid = models.UUIDField("UUID", default=uuid4, unique=True, editable=False)
    order = models.OneToOneField(
        Order, on_delete=models.PROTECT, related_name="sale", verbose_name="pedido"
    )
    cash_session = models.ForeignKey(
        CashRegisterSession, on_delete=models.PROTECT, related_name="sales", verbose_name="turno"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="sales", verbose_name="registrada por"
    )
    payment_method = models.CharField(
        "método de pago", max_length=10, choices=PaymentMethod.choices
    )
    charged_total = models.DecimalField("total cobrado", max_digits=10, decimal_places=2)
    server_total = models.DecimalField("total del servidor", max_digits=10, decimal_places=2)
    needs_review = models.BooleanField("requiere revisión", default=False)
    review_reasons = models.JSONField(
        "motivos de revisión", default=list, blank=True, validators=[validate_review_reasons]
    )
    reviewed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="reviewed_sales",
        null=True, blank=True, verbose_name="revisada por",
    )
    reviewed_at = models.DateTimeField("fecha de revisión", null=True, blank=True)
    device_timestamp = models.DateTimeField("hora del dispositivo")
    server_timestamp = models.DateTimeField("hora del servidor", auto_now_add=True)

    class Meta:
        db_table = "sales"
        verbose_name = "venta"
        verbose_name_plural = "ventas"

    def __str__(self):
        return f"Venta {self.uuid} (${self.charged_total})"


# ---------- Cuarentena ----------
class QuarantinedOperation(models.Model):
    uuid = models.UUIDField("UUID", unique=True)
    operation_type = models.CharField(
        "tipo de operación", max_length=20, choices=OperationType.choices
    )
    payload = models.JSONField("contenido original")
    reason = models.CharField("motivo", max_length=30, choices=QuarantineReason.choices)
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="quarantined_operations",
        null=True, blank=True, verbose_name="usuario que la registró",
    )
    device_timestamp = models.DateTimeField("hora del dispositivo")
    server_timestamp = models.DateTimeField("hora del servidor", auto_now_add=True)
    status = models.CharField(
        "estado", max_length=10, choices=QuarantineStatus.choices, default=QuarantineStatus.PENDING
    )
    resolution = models.CharField(
        "resolución", max_length=20, choices=QuarantineResolution.choices, blank=True
    )
    resolved_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="resolved_quarantines",
        null=True, blank=True, verbose_name="resuelta por",
    )
    resolved_at = models.DateTimeField("fecha de resolución", null=True, blank=True)
    sale = models.ForeignKey(
        Sale, on_delete=models.PROTECT, null=True, blank=True,
        related_name="quarantine_records", verbose_name="venta",
    )
    cash_session = models.ForeignKey(
        CashRegisterSession, on_delete=models.PROTECT, null=True, blank=True,
        related_name="quarantine_records", verbose_name="turno",
    )

    class Meta:
        db_table = "quarantined_operations"
        verbose_name = "operación en cuarentena"
        verbose_name_plural = "operaciones en cuarentena"

    def __str__(self):
        return f"{self.get_operation_type_display()} {self.uuid} ({self.get_reason_display()})"