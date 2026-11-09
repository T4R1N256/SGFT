"""Unit tests for apps.inventory. Whoever implements a service writes its tests."""
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from apps.catalog.models import Category, Dish, Ingredient, Recipe, Units
from apps.inventory.models import MovementKind, StockMovement
from apps.inventory.services import (
    AlreadyDeductedError, InvalidQuantityError, MissingRecipeError, UnknownDishError, check_min_stock,
    deduct_for_sale, is_low_stock, record_sale_return, register_purchase, register_waste, revert_sale_deduction,
    sale_was_deducted,
)

class StockMovementModelTests(TestCase):
    """WBS 3.2.5–3.2.7 — restricciones del modelo de movimientos (autor: Jesús)."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="dueno", password="x-9Lq!pr2", role="admin")
        self.ingredient = Ingredient.objects.create(name="Tortilla de harina", unit=Units.PIECE)

    def movement(self, kind, quantity, **fields):
        return StockMovement.objects.create(ingredient=self.ingredient, kind=kind, quantity=Decimal(quantity),
                                            created_by=self.user, **fields)

    def assertRejected(self, kind, quantity, **fields):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.movement(kind, quantity, **fields)

    def test_purchase_adds_and_keeps_its_cost(self):
        movement = self.movement(MovementKind.PURCHASE, "40", unit_cost=Decimal("2.50"))
        self.assertEqual(movement.unit_cost, Decimal("2.50"))
        self.assertRejected(MovementKind.PURCHASE, "-1")

    def test_sale_and_waste_subtract(self):
        self.movement(MovementKind.SALE, "-1.000", sale_uuid=uuid4())
        self.movement(MovementKind.WASTE, "-0.250", note="Se quemó")
        self.assertRejected(MovementKind.SALE, "1", sale_uuid=uuid4())
        self.assertRejected(MovementKind.WASTE, "2")

    def test_sale_needs_its_uuid(self):
        self.assertRejected(MovementKind.SALE, "-1")

    def test_adjustment_goes_either_way_but_never_zero(self):
        self.movement(MovementKind.ADJUSTMENT, "3")
        self.movement(MovementKind.ADJUSTMENT, "-3")
        self.assertRejected(MovementKind.ADJUSTMENT, "0")

    def test_unit_cost_cannot_be_negative(self):
        self.assertRejected(MovementKind.PURCHASE, "1", unit_cost=Decimal("-0.01"))

    def test_quantity_keeps_three_decimals(self):
        movement = self.movement(MovementKind.WASTE, "-0.005")
        movement.refresh_from_db()
        self.assertEqual(movement.quantity, Decimal("-0.005"))

    def test_ingredient_with_movements_cannot_be_deleted(self):
        self.movement(MovementKind.PURCHASE, "1")
        with self.assertRaises(ProtectedError):
            self.ingredient.delete()

    def test_newest_first(self):
        first = self.movement(MovementKind.PURCHASE, "1")
        second = self.movement(MovementKind.PURCHASE, "2")
        self.assertEqual(list(StockMovement.objects.all()), [second, first])


class DeductForSaleTests(TestCase):
    """WBS 3.2.6 — descuento de inventario al vender (reglas 1, 2 y 10)."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="caja", password="Clave12345")
        category = Category.objects.create(name="Burritos")
        self.burrito = Dish.objects.create(name="Burrito de asada", category=category, price=Decimal("70.00"))
        self.soda = Dish.objects.create(name="Refresco", category=category, price=Decimal("25.00"))
        self.tortilla = Ingredient.objects.create(name="Tortilla", unit=Units.PIECE, stock=Decimal("10"))
        self.beef = Ingredient.objects.create(name="Asada", unit=Units.G, stock=Decimal("1000"))
        self.onion = Ingredient.objects.create(name="Cebolla", unit=Units.G, stock=Decimal("200"))
        self.can = Ingredient.objects.create(name="Lata de refresco", unit=Units.PIECE, stock=Decimal("1"))
        for dish, ingredient, quantity in [(self.burrito, self.tortilla, "1"), (self.burrito, self.beef, "150"),
                                           (self.burrito, self.onion, "20"), (self.soda, self.can, "1")]:
            Recipe.objects.create(dish=dish, ingredient=ingredient, quantity=Decimal(quantity))
        self.uuid = uuid4()

    def stock(self, ingredient):
        ingredient.refresh_from_db()
        return ingredient.stock

    def test_follows_the_recipe_times_the_units(self):
        deduct_for_sale(self.uuid, [{"dish_id": self.burrito.pk, "quantity": 2}], self.user)
        self.assertEqual(self.stock(self.tortilla), Decimal("8"))
        self.assertEqual(self.stock(self.beef), Decimal("700"))
        self.assertEqual(self.stock(self.onion), Decimal("160"))

    def test_leaves_one_sale_movement_per_ingredient(self):
        deduct_for_sale(self.uuid, [{"dish_id": self.burrito.pk, "quantity": 1},
                                    {"dish_id": self.burrito.pk, "quantity": 2}], self.user)
        movements = StockMovement.objects.filter(sale_uuid=self.uuid)
        self.assertEqual(movements.count(), 3)
        self.assertEqual(movements.get(ingredient=self.beef).quantity, Decimal("-450"))
        self.assertTrue(all(m.kind == MovementKind.SALE and m.created_by == self.user for m in movements))

    def test_removed_ingredient_is_not_deducted(self):
        deduct_for_sale(self.uuid, [{"dish_id": self.burrito.pk, "quantity": 2,
                                     "modifiers": [{"ingredient_id": self.onion.pk, "kind": "remove"}]}], self.user)
        self.assertEqual(self.stock(self.onion), Decimal("200"))
        self.assertFalse(StockMovement.objects.filter(ingredient=self.onion).exists())

    def test_extra_deducts_its_quantity_per_unit(self):
        extra = {"ingredient_id": self.beef.pk, "kind": "add", "quantity": Decimal("50")}
        deduct_for_sale(self.uuid, [{"dish_id": self.burrito.pk, "quantity": 2, "modifiers": [extra]}], self.user)
        self.assertEqual(self.stock(self.beef), Decimal("600"))  # 1000 - (150 + 50) × 2

    def test_stock_may_go_negative_and_is_reported(self):
        negative = deduct_for_sale(self.uuid, [{"dish_id": self.soda.pk, "quantity": 3}], self.user)
        self.assertEqual(self.stock(self.can), Decimal("-2"))
        self.assertEqual(negative, [self.can])

    def test_nothing_negative_reports_nothing(self):
        self.assertEqual(deduct_for_sale(self.uuid, [{"dish_id": self.soda.pk, "quantity": 1}], self.user), [])

    def test_dish_without_recipe_changes_nothing(self):
        salad = Dish.objects.create(name="Ensalada", category=self.burrito.category, price=Decimal("40.00"))
        with self.assertRaises(MissingRecipeError) as error:
            deduct_for_sale(self.uuid, [{"dish_id": self.burrito.pk, "quantity": 1},
                                        {"dish_id": salad.pk, "quantity": 1}], self.user)
        self.assertEqual(error.exception.dish_ids, [salad.pk])
        self.assertEqual(self.stock(self.tortilla), Decimal("10"))
        self.assertFalse(StockMovement.objects.exists())

    def test_unknown_dish_is_rejected(self):
        with self.assertRaises(UnknownDishError):
            deduct_for_sale(self.uuid, [{"dish_id": 9999, "quantity": 1}], self.user)

    def test_same_sale_is_deducted_only_once(self):
        lines = [{"dish_id": self.soda.pk, "quantity": 1}]
        deduct_for_sale(self.uuid, lines, self.user)
        with self.assertRaises(AlreadyDeductedError):
            deduct_for_sale(self.uuid, lines, self.user)
        self.assertEqual(self.stock(self.can), Decimal("0"))

    def test_revert_gives_the_stock_back_as_an_adjustment(self):
        lines = [{"dish_id": self.burrito.pk, "quantity": 2}]
        deduct_for_sale(self.uuid, lines, self.user)
        revert_sale_deduction(self.uuid, [{"dish_id": self.burrito.pk, "quantity": 1}], self.user, "Error de captura")
        self.assertEqual(self.stock(self.beef), Decimal("850"))
        adjustment = StockMovement.objects.get(ingredient=self.beef, kind=MovementKind.ADJUSTMENT)
        self.assertEqual((adjustment.quantity, adjustment.sale_uuid, adjustment.note),
                         (Decimal("150"), self.uuid, "Error de captura"))

    def test_return_records_the_ingredients_as_waste_without_changing_stock(self):
        deduct_for_sale(self.uuid, [{"dish_id": self.burrito.pk, "quantity": 2}], self.user)
        record_sale_return(self.uuid, [{"dish_id": self.burrito.pk, "quantity": 1}], self.user, "Devolución")
        self.assertEqual(self.stock(self.beef), Decimal("700"))
        waste = StockMovement.objects.get(ingredient=self.beef, kind=MovementKind.WASTE)
        adjustment = StockMovement.objects.get(ingredient=self.beef, kind=MovementKind.ADJUSTMENT)
        self.assertEqual((waste.quantity, waste.sale_uuid, adjustment.quantity),
                         (Decimal("-150"), self.uuid, Decimal("150")))

    def test_sale_was_deducted(self):
        self.assertFalse(sale_was_deducted(self.uuid))
        deduct_for_sale(self.uuid, [{"dish_id": self.soda.pk, "quantity": 1}], self.user)
        self.assertTrue(sale_was_deducted(self.uuid))



class PurchaseWasteAndAlertTests(TestCase):
    """WBS 3.2.5, 3.2.7 y 3.2.8 — compras, mermas y alerta de mínimo (regla 3)."""

    def setUp(self):
        self.admin = get_user_model().objects.create_user(username="dueno", password="x-9Lq!pr2", role="admin")
        self.beans = Ingredient.objects.create(name="Frijoles", unit=Units.KG, stock=Decimal("2"),
                                               min_stock=Decimal("1.5"), unit_cost=Decimal("30.00"))

    def stock(self):
        self.beans.refresh_from_db()
        return self.beans.stock

    def test_purchase_adds_stock_and_updates_the_cost(self):
        movement = register_purchase(self.beans, Decimal("5.250"), Decimal("32.50"), self.admin, note="Mercado")
        self.assertEqual(self.stock(), Decimal("7.250"))
        self.assertEqual(self.beans.unit_cost, Decimal("32.50"))
        self.assertEqual((movement.kind, movement.quantity, movement.unit_cost, movement.created_by),
                         (MovementKind.PURCHASE, Decimal("5.250"), Decimal("32.50"), self.admin))

    def test_purchase_rejects_zero_negative_or_too_precise_quantities(self):
        for quantity in ["0", "-1", "0.0005", "abc"]:
            with self.subTest(quantity=quantity), self.assertRaises(InvalidQuantityError):
                register_purchase(self.beans, quantity, Decimal("30.00"), self.admin)
        self.assertEqual(self.stock(), Decimal("2"))
        self.assertFalse(StockMovement.objects.exists())

    def test_purchase_rejects_a_negative_cost(self):
        with self.assertRaises(InvalidQuantityError):
            register_purchase(self.beans, Decimal("1"), Decimal("-1.00"), self.admin)

    def test_waste_subtracts_with_its_reason(self):
        movement = register_waste(self.beans, Decimal("0.5"), self.admin, "  Se agrió  ")
        self.assertEqual(self.stock(), Decimal("1.5"))
        self.assertEqual((movement.kind, movement.quantity, movement.note),
                         (MovementKind.WASTE, Decimal("-0.5"), "Se agrió"))

    def test_waste_needs_a_reason(self):
        with self.assertRaises(InvalidQuantityError):
            register_waste(self.beans, Decimal("0.5"), self.admin, " ")
        self.assertEqual(self.stock(), Decimal("2"))

    def test_waste_may_leave_stock_negative(self):
        register_waste(self.beans, Decimal("3"), self.admin, "Se cayó la olla")
        self.assertEqual(self.stock(), Decimal("-1"))

    def test_alert_when_stock_reaches_the_minimum(self):
        self.assertFalse(is_low_stock(self.beans))
        register_waste(self.beans, Decimal("0.5"), self.admin, "Se agrió")
        self.assertTrue(is_low_stock(self.beans))  # 1.5 <= 1.5

    def test_check_min_stock_lists_the_most_urgent_first(self):
        tortilla = Ingredient.objects.create(name="Tortilla", unit=Units.PIECE, stock=Decimal("-3"),
                                             min_stock=Decimal("20"))
        cheese = Ingredient.objects.create(name="Queso", unit=Units.KG, stock=Decimal("1"), min_stock=Decimal("1"))
        Ingredient.objects.create(name="Sal", unit=Units.KG, stock=Decimal("5"), min_stock=Decimal("1"))
        self.assertEqual(list(check_min_stock()), [tortilla, cheese])