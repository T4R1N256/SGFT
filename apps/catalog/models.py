"""
Catalog and recipe models for SGFT (WBS 3.2.1, 3.2.2, 3.2.3).
"""
from django.db import models


class Units(models.TextChoices):
    """Unidades de medida estandarizadas para el inventario e insumos (DEC-30)."""
    KG = "kg", "Kilogramos"
    G = "g", "Gramos"
    L = "L", "Litros"
    ML = "ml", "Mililitros"
    PIECE = "pzas", "Piezas"


class Category(models.Model):
    """Categorías para clasificar los platillos del catálogo."""
    name = models.CharField("nombre", max_length=100, unique=True)
    emoji = models.CharField("emoji", max_length=8, blank=True)

    class Meta:
        db_table = "categories"
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.name


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
    description = models.TextField("descripción", blank=True)
    is_active = models.BooleanField("activo", default=True)

    class Meta:
        db_table = "dishes"
        verbose_name = "platillo"
        verbose_name_plural = "platillos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="dish_price_gte_0"
            )
        ]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Insumos o materia prima. Existencia puede ser negativa (Regla 10 / WBS 3.2.2)."""
    name = models.CharField("nombre", max_length=150, unique=True)
    unit = models.CharField(
        "unidad de medida",
        max_length=10,
        choices=Units.choices
    )
    min_stock = models.DecimalField(
        "stock mínimo",
        max_digits=10,
        decimal_places=3,
        default=0
    )
    unit_cost = models.DecimalField(
        "costo unitario",
        max_digits=10,
        decimal_places=2,
        default=0
    )
    stock = models.DecimalField(
        "existencia",
        max_digits=10,
        decimal_places=3,
        default=0,
        help_text="Cantidad actual en inventario (puede ser negativa)."
    )

    class Meta:
        db_table = "ingredients"
        verbose_name = "insumo"
        verbose_name_plural = "insumos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(unit_cost__gte=0),
                name="ingredient_unit_cost_gte_0"
            ),
            models.CheckConstraint(
                condition=models.Q(min_stock__gte=0),
                name="ingredient_min_stock_gte_0"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"


class Recipe(models.Model):
    """Asociación de platillo e insumo con su cantidad para costeo y descuento (WBS 3.2.3)."""
    dish = models.ForeignKey(
        Dish,
        on_delete=models.PROTECT,
        related_name="recipes",
        verbose_name="platillo"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="recipes",
        verbose_name="insumo"
    )
    quantity = models.DecimalField("cantidad requerida", max_digits=10, decimal_places=3)

    class Meta:
        db_table = "recipes"
        verbose_name = "receta"
        verbose_name_plural = "recetas"
        constraints = [
            models.UniqueConstraint(
                fields=["dish", "ingredient"],
                name="unique_dish_ingredient"
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="recipe_quantity_gt_0"
            ),
        ]

    def __str__(self):
        return f"{self.dish.name} - {self.ingredient.name} ({self.quantity} {self.ingredient.unit})"