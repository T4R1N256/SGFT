"""
Inventory services (WBS 3.2.5–3.2.8). Owner: Diego.

deduct_for_sale is called by pos.services.confirm_sale inside the same atomic transaction that saves the sale
(rule 1): online when the sale is charged, offline when it syncs. inventory never imports pos (CLAUDE.md §7), so
the sale arrives as its UUID plus plain lines:

    [{"dish_id": 3, "quantity": 2,
      "modifiers": [{"ingredient_id": 7, "kind": "remove"},
                    {"ingredient_id": 9, "kind": "add", "quantity": Decimal("30")}]}]

"quantity" of an "add" modifier is how much of the ingredient one extra uses (pos.Modifier.quantity).
"""
from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.db.models import F

from apps.catalog.models import Dish, Ingredient, Recipe
from apps.inventory.models import MovementKind, StockMovement

ADD = "add"
REMOVE = "remove"


class MissingRecipeError(Exception):
    """A dish of the sale has no recipe, so there is nothing to deduct. Offline, it goes to quarantine."""

    def __init__(self, dish_ids):
        self.dish_ids = sorted(dish_ids)
        super().__init__(f"Platillos sin receta: {', '.join(map(str, self.dish_ids))}.")


class UnknownDishError(Exception):
    """A line names a dish that does not exist."""

    def __init__(self, dish_ids):
        self.dish_ids = sorted(dish_ids)
        super().__init__(f"Platillos desconocidos: {', '.join(map(str, self.dish_ids))}.")


class AlreadyDeductedError(Exception):
    """The sale was already deducted: a UUID is deducted only once."""


def required_quantities(lines):
    """
    {ingredient_id: Decimal} that the lines use, following each recipe (ingredient × quantity × units, rule 1).
    A removed ingredient is not counted for that line; an extra adds its quantity × units (rule 2).
    """
    dish_ids = {line["dish_id"] for line in lines}
    known = set(Dish.objects.filter(pk__in=dish_ids).values_list("pk", flat=True))
    if dish_ids - known:
        raise UnknownDishError(dish_ids - known)
    recipes = defaultdict(list)
    for dish_id, ingredient_id, quantity in Recipe.objects.filter(dish_id__in=dish_ids).values_list(
            "dish_id", "ingredient_id", "quantity"):
        recipes[dish_id].append((ingredient_id, quantity))
    if dish_ids - set(recipes):
        raise MissingRecipeError(dish_ids - set(recipes))

    needed = defaultdict(Decimal)
    for line in lines:
        units = line["quantity"]
        modifiers = line.get("modifiers", [])
        removed = {m["ingredient_id"] for m in modifiers if m["kind"] == REMOVE}
        for ingredient_id, quantity in recipes[line["dish_id"]]:
            if ingredient_id not in removed:
                needed[ingredient_id] += quantity * units
        for modifier in modifiers:
            if modifier["kind"] == ADD and modifier.get("quantity"):
                needed[modifier["ingredient_id"]] += Decimal(modifier["quantity"]) * units
    return {ingredient_id: quantity for ingredient_id, quantity in needed.items() if quantity}


def _apply(quantities, kind, user, sale_uuid=None, note=""):
    """Adds the signed quantities to the stock, one StockMovement each. Locks the rows in pk order."""
    ingredients = Ingredient.objects.select_for_update().filter(pk__in=quantities).order_by("pk")
    changed = []
    for ingredient in ingredients:
        quantity = quantities[ingredient.pk]
        Ingredient.objects.filter(pk=ingredient.pk).update(stock=F("stock") + quantity)
        StockMovement.objects.create(ingredient=ingredient, kind=kind, quantity=quantity, sale_uuid=sale_uuid,
                                     note=note, created_by=user)
        changed.append(ingredient.pk)
    return list(Ingredient.objects.filter(pk__in=changed).order_by("name"))


@transaction.atomic
def deduct_for_sale(sale_uuid, lines, user):
    """
    Deducts what the sale used and returns the ingredients whose stock is now negative. A negative stock is
    allowed (rule 10): the sale is not reverted, and the caller marks it for review (existencia_negativa).
    Raises UnknownDishError, MissingRecipeError or AlreadyDeductedError and then changes nothing.
    """
    if StockMovement.objects.filter(sale_uuid=sale_uuid, kind=MovementKind.SALE).exists():
        raise AlreadyDeductedError(f"La venta {sale_uuid} ya descontó inventario.")
    quantities = {pk: -quantity for pk, quantity in required_quantities(lines).items()}
    changed = _apply(quantities, MovementKind.SALE, user, sale_uuid=sale_uuid)
    return [ingredient for ingredient in changed if ingredient.stock < 0]


@transaction.atomic
def revert_sale_deduction(sale_uuid, lines, user, note):
    """
    Gives back to the stock what lines used, as an adjustment linked to the sale. It is how a cancellation or
    an adjustment for error_captura reverts inventory (rule 11); lines can be the whole sale or the adjusted
    units of one line. Returns the ingredients that changed.
    """
    return _apply(required_quantities(lines), MovementKind.ADJUSTMENT, user, sale_uuid=sale_uuid, note=note)


@transaction.atomic
def record_sale_return(sale_uuid, lines, user, note):
    """
    A return (devolucion, rule 11): the money goes back but the food is not, so what lines used is recorded as
    waste instead of a sale. It leaves an adjustment that gives the quantity back and a waste that takes it out
    again, both linked to the sale: the stock does not change, but the waste report counts it. Returns the
    waste movements' ingredients.
    """
    quantities = required_quantities(lines)
    _apply(quantities, MovementKind.ADJUSTMENT, user, sale_uuid=sale_uuid, note=note)
    return _apply({pk: -quantity for pk, quantity in quantities.items()}, MovementKind.WASTE, user,
                  sale_uuid=sale_uuid, note=note)


def sale_was_deducted(sale_uuid):
    """True if the sale deducted inventory (a sale applied without deduction from quarantine did not)."""
    return StockMovement.objects.filter(sale_uuid=sale_uuid, kind=MovementKind.SALE).exists()


class InvalidQuantityError(ValueError):
    """A purchase or waste quantity must be greater than zero, in the ingredient's unit, with up to 3 decimals."""


# ---------- Compras, mermas y alertas (WBS 3.2.5, 3.2.7, 3.2.8) ----------
def _positive(value, field, places):
    try:
        value = Decimal(value)
    except (ArithmeticError, TypeError, ValueError):
        raise InvalidQuantityError(f"{field} debe ser un número.") from None
    if not value.is_finite() or value <= 0 or value != value.quantize(Decimal(1).scaleb(-places)):
        raise InvalidQuantityError(f"{field} debe ser mayor que cero y tener a lo más {places} decimales.")
    return value


@transaction.atomic
def register_purchase(ingredient, quantity, unit_cost, user, note=""):
    """
    Brings quantity (in the ingredient's unit) into the stock. unit_cost is what one unit cost in this purchase;
    it becomes the ingredient's unit_cost, so the dish cost follows the latest price. Returns the movement.
    """
    quantity = _positive(quantity, "La cantidad", 3)
    unit_cost = Decimal(unit_cost)
    if not unit_cost.is_finite() or unit_cost < 0 or unit_cost != unit_cost.quantize(Decimal("0.01")):
        raise InvalidQuantityError("El costo unitario no puede ser negativo y lleva a lo más 2 decimales.")
    Ingredient.objects.select_for_update().filter(pk=ingredient.pk).update(stock=F("stock") + quantity,
                                                                           unit_cost=unit_cost)
    ingredient.refresh_from_db(fields=["stock", "unit_cost"])
    return StockMovement.objects.create(ingredient=ingredient, kind=MovementKind.PURCHASE, quantity=quantity,
                                        unit_cost=unit_cost, note=note, created_by=user)


@transaction.atomic
def register_waste(ingredient, quantity, user, note):
    """
    Takes quantity out of the stock as waste (spoiled, burnt, returned). The reason is required. The stock may
    go negative, as with a sale (rule 10). Returns the movement.
    """
    quantity = _positive(quantity, "La cantidad", 3)
    if not note or not note.strip():
        raise InvalidQuantityError("Escribe el motivo de la merma.")
    Ingredient.objects.select_for_update().filter(pk=ingredient.pk).update(stock=F("stock") - quantity)
    ingredient.refresh_from_db(fields=["stock"])
    return StockMovement.objects.create(ingredient=ingredient, kind=MovementKind.WASTE, quantity=-quantity,
                                        note=note.strip(), created_by=user)


def is_low_stock(ingredient):
    """Rule 3: the alert shows when stock <= min_stock. It is only visual; it never blocks a sale."""
    return ingredient.stock <= ingredient.min_stock


def check_min_stock():
    """Ingredients at or below their minimum (rule 3), the most urgent first: negative stock, then by name."""
    return Ingredient.objects.filter(stock__lte=F("min_stock")).order_by("stock", "name")
