"""Unit tests for apps.inventory. Whoever implements a service writes its tests."""
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from apps.catalog.models import Ingredient, Units
from apps.inventory.models import MovementKind, StockMovement


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
