"""
Catalog services: dishes and their prices, ingredients and recipes (WBS 3.2.1–3.2.3). Owner: Diego.

Only the Administrator defines prices, recipes and minimums (rule 6); the view checks the role, these functions
check the data. Every function validates with full_clean(), so a wrong value raises ValidationError with the
message in Spanish, ready to show next to the field.

Nothing here is ever deleted: a dish leaves the menu with is_active=False and an ingredient stays because sales
and movements point to it. The stock of an ingredient is not edited here: it only changes through the
inventory services, which leave a StockMovement for each change.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.catalog.models import Dish, Ingredient, Recipe

DISH_FIELDS = ("name", "category", "price", "description", "is_active")
INGREDIENT_FIELDS = ("name", "unit", "min_stock", "unit_cost")


def _save(instance):
    instance.full_clean()
    instance.save()
    return instance


def _set_fields(instance, fields, allowed):
    unknown = set(fields) - set(allowed)
    if unknown:
        raise ValueError(f"Campos que no se pueden cambiar aquí: {', '.join(sorted(unknown))}.")
    for name, value in fields.items():
        setattr(instance, name, value)


# Platillos
def create_dish(name, category, price, description="", is_active=True):
    """Adds a dish to the menu. price is a Decimal with two decimals and cannot be negative."""
    return _save(Dish(name=name, category=category, price=price, description=description, is_active=is_active))


def update_dish(dish, **fields):
    """Changes name, category, price, description or is_active. The sales already charged keep their price."""
    _set_fields(dish, fields, DISH_FIELDS)
    return _save(dish)


def set_dish_active(dish, is_active):
    """Shows or hides a dish in Nueva venta. A dish is never deleted: past sales point to it."""
    dish.is_active = is_active
    dish.save(update_fields=["is_active"])
    return dish


def active_dishes():
    """Dishes offered in Nueva venta, by category and name."""
    return Dish.objects.filter(is_active=True).select_related("category").order_by("category__name", "name")


# Insumos 
def create_ingredient(name, unit, min_stock=Decimal("0"), unit_cost=Decimal("0")):
    """Adds an ingredient with stock 0. The first purchase (inventory.register_purchase) brings it in."""
    return _save(Ingredient(name=name, unit=unit, min_stock=min_stock, unit_cost=unit_cost))


def update_ingredient(ingredient, **fields):
    """
    Changes name, unit, min_stock or unit_cost; the stock cannot be set here. The unit cannot change once the
    ingredient is in a recipe or has movements, because those quantities were written in the old unit.
    """
    _set_fields(ingredient, fields, INGREDIENT_FIELDS)
    if "unit" in fields:
        stored_unit = Ingredient.objects.filter(pk=ingredient.pk).values_list("unit", flat=True).first()
        # movements is the reverse name of inventory.StockMovement; reading it needs no import of inventory.
        in_use = ingredient.recipes.exists() or ingredient.movements.exists()
        if stored_unit and stored_unit != ingredient.unit and in_use:
            raise ValidationError({"unit": "No se puede cambiar la unidad de un insumo que ya está en una "
                                           "receta o tiene movimientos."})
    return _save(ingredient)


# Recetas 
@transaction.atomic
def set_recipe(dish, items):
    """
    Replaces the whole recipe of dish with items: a list of (ingredient, quantity) pairs, quantity in the
    ingredient's unit and greater than zero. Either the whole recipe is saved or nothing changes.
    """
    if not items:
        raise ValidationError("La receta necesita al menos un insumo; sin receta no se descuenta inventario.")
    seen = set()
    for ingredient, quantity in items:
        if ingredient.pk in seen:
            raise ValidationError(f"El insumo {ingredient.name} está repetido en la receta.")
        seen.add(ingredient.pk)
        if quantity is None or quantity <= 0:
            raise ValidationError(f"La cantidad de {ingredient.name} debe ser mayor que cero.")
    Recipe.objects.filter(dish=dish).delete()
    rows = [Recipe(dish=dish, ingredient=ingredient, quantity=quantity) for ingredient, quantity in items]
    for row in rows:
        row.full_clean(validate_unique=False)  # duplicates were checked above; the old rows are being replaced
    Recipe.objects.bulk_create(rows)
    return list(dish.recipes.select_related("ingredient").order_by("ingredient__name"))


def dish_cost(dish):
    """What the ingredients of one unit of dish cost, with today's unit_cost: the base of its margin."""
    total = sum((row.quantity * row.ingredient.unit_cost for row in dish.recipes.select_related("ingredient")),
                Decimal("0"))
    return total.quantize(Decimal("0.01"))


def dish_margin(dish):
    """Price minus cost of one unit of dish."""
    return dish.price - dish_cost(dish)