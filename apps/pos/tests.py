"""Unit tests for apps.pos. Whoever implements a service writes its tests."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Category, Dish, Ingredient, Units
from apps.pos.models import (
    CashRegisterSession, Modifier, Order, OrderItem, QuarantinedOperation,
    QuarantineReason, ReviewReason, Sale, validate_review_reasons,
)


class PosModelsBase(TestCase):
    """Datos mínimos para probar las restricciones de los modelos de pos."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="caja1", password="Clave12345")
        self.category = Category.objects.create(name="Tacos")
        self.dish = Dish.objects.create(
            name="Taco de asada", category=self.category, price=Decimal("85.00")
        )
        self.ingredient = Ingredient.objects.create(name="Tortilla", unit=Units.values[0])

    def make_session(self, **kwargs):
        data = dict(
            business_date=date(2026, 10, 1), opened_by=self.user,
            opening_amount=Decimal("500.00"), device_timestamp=timezone.now(),
        )
        data.update(kwargs)
        return CashRegisterSession.objects.create(**data)

    def make_order(self):
        return Order.objects.create(created_by=self.user)

    def make_sale(self, order=None, session=None, **kwargs):
        data = dict(
            order=order or self.make_order(), cash_session=session or self.make_session(),
            created_by=self.user, payment_method="cash", charged_total=Decimal("100.00"),
            server_total=Decimal("100.00"), device_timestamp=timezone.now(),
        )
        data.update(kwargs)
        return Sale.objects.create(**data)


class CashRegisterSessionTests(PosModelsBase):
    def test_uuid_is_unique(self):
        first = self.make_session(status="closed")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_session(uuid=first.uuid, business_date=date(2026, 10, 2), status="closed")

    def test_only_one_session_per_day(self):
        self.make_session(status="closed")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_session(status="closed")  # misma fecha de negocio

    def test_only_one_open_session_at_a_time(self):
        self.make_session(business_date=date(2026, 10, 1), status="open")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_session(business_date=date(2026, 10, 2), status="open")

    def test_several_closed_sessions_are_allowed(self):
        self.make_session(business_date=date(2026, 10, 1), status="closed")
        self.make_session(business_date=date(2026, 10, 2), status="closed")
        self.assertEqual(CashRegisterSession.objects.count(), 2)

    def test_opening_amount_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_session(opening_amount=Decimal("-0.01"))

    def test_closing_amount_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_session(status="closed", closing_amount=Decimal("-0.01"))

    def test_zero_amounts_are_accepted(self):
        session = self.make_session(
            status="closed", opening_amount=Decimal("0.00"), closing_amount=Decimal("0.00")
        )
        self.assertEqual(session.closing_amount, Decimal("0.00"))


class OrderItemTests(PosModelsBase):
    def test_quantity_zero_is_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            OrderItem.objects.create(
                order=self.make_order(), dish=self.dish, quantity=0, unit_price=Decimal("85.00")
            )

    def test_quantity_one_is_accepted(self):
        item = OrderItem.objects.create(
            order=self.make_order(), dish=self.dish, quantity=1, unit_price=Decimal("85.00")
        )
        self.assertEqual(item.quantity, 1)

    def test_dish_with_order_items_cannot_be_deleted(self):
        OrderItem.objects.create(
            order=self.make_order(), dish=self.dish, quantity=1, unit_price=Decimal("85.00")
        )
        with self.assertRaises(ProtectedError):
            self.dish.delete()

    def test_unit_price_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            OrderItem.objects.create(
                order=self.make_order(), dish=self.dish, quantity=1, unit_price=Decimal("-0.01")
            )

    def test_unit_price_zero_is_accepted(self):
        item = OrderItem.objects.create(
            order=self.make_order(), dish=self.dish, quantity=1, unit_price=Decimal("0.00")
        )
        self.assertEqual(item.unit_price, Decimal("0.00"))


class ModifierTests(PosModelsBase):
    def test_same_dish_ingredient_kind_is_rejected(self):
        Modifier.objects.create(dish=self.dish, ingredient=self.ingredient, kind="add")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Modifier.objects.create(dish=self.dish, ingredient=self.ingredient, kind="add")

    def test_other_kind_is_allowed(self):
        Modifier.objects.create(dish=self.dish, ingredient=self.ingredient, kind="add")
        Modifier.objects.create(dish=self.dish, ingredient=self.ingredient, kind="remove")
        self.assertEqual(Modifier.objects.count(), 2)

    def test_quantity_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Modifier.objects.create(
                dish=self.dish, ingredient=self.ingredient, kind="add",
                quantity=Decimal("-0.001"),
            )


class SaleTests(PosModelsBase):
    def test_uuid_is_unique(self):
        first = self.make_sale()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_sale(uuid=first.uuid, session=first.cash_session)

    def test_order_has_only_one_sale(self):
        order = self.make_order()
        session = self.make_session()
        self.make_sale(order=order, session=session)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_sale(order=order, session=session)

    def test_session_with_sales_cannot_be_deleted(self):
        sale = self.make_sale()
        with self.assertRaises(ProtectedError):
            sale.cash_session.delete()

    def test_review_reasons_accepts_only_known_values(self):
        validate_review_reasons([ReviewReason.PRICE_DIFFERENT, ReviewReason.NEGATIVE_STOCK])
        with self.assertRaises(ValidationError):
            validate_review_reasons(["inventado"])

    def test_review_reasons_must_be_a_list(self):
        with self.assertRaises(ValidationError):
            validate_review_reasons("precio_distinto")

    def test_charged_total_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_sale(charged_total=Decimal("-0.01"))

    def test_server_total_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_sale(server_total=Decimal("-0.01"))

    def test_zero_totals_are_accepted(self):
        sale = self.make_sale(charged_total=Decimal("0.00"), server_total=Decimal("0.00"))
        self.assertEqual(sale.charged_total, Decimal("0.00"))


class QuarantinedOperationTests(PosModelsBase):
    def make_quarantine(self, **kwargs):
        data = dict(
            uuid="6f1c2a0e-3b7d-4c55-9a51-0d2b8e7f4a10", operation_type="venta",
            payload={"tipo": "venta"}, reason=QuarantineReason.INVALID_SESSION,
            device_timestamp=timezone.now(),
        )
        data.update(kwargs)
        return QuarantinedOperation.objects.create(**data)

    def test_uuid_is_unique(self):
        self.make_quarantine()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_quarantine()

    def test_unknown_reason_is_rejected(self):
        field = QuarantinedOperation._meta.get_field("reason")
        with self.assertRaises(ValidationError):
            field.clean("inventado", None)

    def test_reasons_match_the_contract(self):
        self.assertEqual(
            set(QuarantineReason.values),
            {"usuario_sin_permiso", "turno_ya_abierto", "turno_invalido",
             "platillo_desconocido", "receta_faltante", "total_inconsistente"},
        )