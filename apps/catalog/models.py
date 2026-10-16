"""
Catalog and recipe models for SGFT (WBS 3.2.1, 3.2.2, 3.2.3).
"""
from django.db import models


class Units(models.TextChoices):
    """Unidades de medida estandarizadas para el inventario e insumos (WBS 3.2.2)."""
    KG = "kg", "Kilogramos"
    G = "g", "Gramos"
    L = "L", "Litros"
    ML = "ml", "Mililitros"
    PIECE = "pcs", "Piezas"


class Category(models.Model):
    """Categorías para clasificar los platillos del catálogo."""
    name = models.CharField("nombre", max_length=100, unique=True)

    class Meta:
        db_table = "categories"
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

class Dish(models.Model):
    """Platillo o producto ofertado en el catálogo del POS (WBS 3.2.1)."""
    name = models.CharField("nombre", max_length=150)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="dishes",
        verbose_name="categoría"
    )
    price = models.DecimalField("precio", max_digits=10, decimal_places=2)
    description = models.TextField("descripción", blank=True, null=True)
    is_active = models.BooleanField("activo", default=True)

    class Meta:
        db_table = "dishes"
        verbose_name = "platillo"
        verbose_name_plural = "platillos"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Insumos o materia prima que pueden quedar con existencia negativa (WBS 3.2.2)."""
    name = models.CharField("nombre", max_length=150, unique=True)
    unit = models.CharField(
        "unidad de medida",
        max_length=10,
        choices=Units.choices,
        default=Units.G
    )
    min_stock = models.DecimalField("stock mínimo", max_digits=10, decimal_places=2, default=0)
    unit_cost = models.DecimalField("costo unitario", max_digits=10, decimal_places=2)
    stock = models.DecimalField(
        "existencia",
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cantidad actual en inventario."
    )

    class Meta:
        db_table = "ingredients"
        verbose_name = "insumo"
        verbose_name_plural = "insumos"

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"


class Recipe(models.Model):
    """Asociación de platillo e insumo con su cantidad para costeo y descuento (WBS 3.2.3)."""
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="platillo"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="recipes",
        verbose_name="insumo"
    )
    quantity = models.DecimalField("cantidad requerida", max_digits=10, decimal_places=2)

    class Meta:
        db_table = "recipes"
        verbose_name = "receta"
        verbose_name_plural = "recetas"
        unique_together = ("dish", "ingredient")

    def __str__(self):
        return f"{self.dish.name} - {self.ingredient.name} ({self.quantity} {self.ingredient.unit})"