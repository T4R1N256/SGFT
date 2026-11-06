"""StockMovement: purchase / sale / waste / adjustment (WBS 3.2.5–3.2.8). Owner: Jesús, who reviews every change; whoever writes a model generates its migration after telling him (DEC-37)."""

from django.conf import settings
from django.db import models
from django.db.models import Q

User = settings.AUTH_USER_MODEL


class MovementKind(models.TextChoices):
    PURCHASE = "purchase", "Compra"
    SALE = "sale", "Venta"
    WASTE = "waste", "Merma"
    ADJUSTMENT = "adjustment", "Ajuste"


class StockMovement(models.Model):
    """
    Every change to Ingredient.stock leaves one row; the stock itself stays on Ingredient (it may go negative,
    rule 10). quantity is the signed change in the ingredient's unit: a purchase adds, a sale or a waste
    subtracts, an adjustment (e.g. reverting a sale captured by mistake) goes either way.

    The sale is referenced by its UUID and not by a foreign key: inventory never imports pos (CLAUDE.md §7).
    """
    ingredient = models.ForeignKey(
        "catalog.Ingredient", on_delete=models.PROTECT, related_name="movements", verbose_name="insumo"
    )
    kind = models.CharField("tipo", max_length=12, choices=MovementKind.choices)
    quantity = models.DecimalField(
        "cantidad", max_digits=10, decimal_places=3, help_text="Positiva entra, negativa sale."
    )
    unit_cost = models.DecimalField(
        "costo unitario", max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Solo en compras.",
    )
    sale_uuid = models.UUIDField("UUID de la venta", null=True, blank=True, db_index=True)
    note = models.CharField("motivo o nota", max_length=255, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="stock_movements", verbose_name="registrado por"
    )
    created_at = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        db_table = "stock_movements"
        verbose_name = "movimiento de inventario"
        verbose_name_plural = "movimientos de inventario"
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.CheckConstraint(condition=~Q(quantity=0), name="inventory_movement_quantity_not_0"),
            models.CheckConstraint(
                condition=~Q(kind="purchase") | Q(quantity__gt=0), name="inventory_purchase_adds_stock"
            ),
            models.CheckConstraint(
                condition=~Q(kind__in=["sale", "waste"]) | Q(quantity__lt=0),
                name="inventory_sale_and_waste_subtract_stock",
            ),
            models.CheckConstraint(
                condition=Q(unit_cost__isnull=True) | Q(unit_cost__gte=0), name="inventory_unit_cost_gte_0"
            ),
            models.CheckConstraint(
                condition=~Q(kind="sale") | Q(sale_uuid__isnull=False), name="inventory_sale_has_uuid"
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} {self.quantity} de {self.ingredient_id}"
