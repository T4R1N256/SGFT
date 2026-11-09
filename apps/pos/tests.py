"""Unit tests for apps.pos. Whoever implements a service writes its tests."""

import json
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Category, Dish, Ingredient, Units
from apps.pos import services_cash_session as cash
from apps.pos.services_pricing import calcular_total
from apps.pos.models import (
    AdjustmentKind, AdjustmentReason, CashRegisterSession, Modifier, Order, OrderItem, QuarantinedOperation,
    QuarantineReason, ReviewReason, Sale, SaleAdjustment, validate_review_reasons,
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


class SaleAdjustmentTests(PosModelsBase):
    """WBS 3.3.8 — ajustes y cancelaciones que dejan rastro (autor: Jesús)."""

    def setUp(self):
        super().setUp()
        self.sale = self.make_sale()
        self.item = OrderItem.objects.create(order=self.sale.order, dish=self.dish, quantity=2,
                                             unit_price=Decimal("50.00"))

    def adjust(self, **kwargs):
        data = dict(sale=self.sale, kind=AdjustmentKind.ADJUSTMENT, reason=AdjustmentReason.CAPTURE_ERROR,
                    order_item=self.item, quantity=1, amount=Decimal("50.00"), authorized_by=self.user)
        data.update(kwargs)
        return SaleAdjustment.objects.create(**data)

    def assertRejected(self, **kwargs):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.adjust(**kwargs)

    def test_line_adjustment_points_to_the_original_sale(self):
        adjustment = self.adjust()
        self.assertEqual(list(self.sale.adjustments.all()), [adjustment])

    def test_cancellation_covers_the_whole_sale_once(self):
        self.adjust(kind=AdjustmentKind.CANCELLATION, order_item=None, quantity=None, amount=Decimal("100.00"))
        self.assertRejected(kind=AdjustmentKind.CANCELLATION, order_item=None, quantity=None)

    def test_cancellation_cannot_name_a_line(self):
        self.assertRejected(kind=AdjustmentKind.CANCELLATION)

    def test_payment_correction_only_changes_the_method(self):
        self.adjust(reason=AdjustmentReason.PAYMENT_CORRECTION, order_item=None, quantity=None, amount=0,
                    new_payment_method="transfer")
        self.assertRejected(reason=AdjustmentReason.PAYMENT_CORRECTION, order_item=None, quantity=None, amount=0)
        self.assertRejected(reason=AdjustmentReason.PAYMENT_CORRECTION, order_item=None, quantity=None,
                            new_payment_method="transfer")

    def test_only_payment_correction_sets_a_new_method(self):
        self.assertRejected(new_payment_method="transfer")

    def test_line_adjustment_needs_line_and_quantity(self):
        self.assertRejected(order_item=None)
        self.assertRejected(quantity=0)

    def test_amount_cannot_be_negative(self):
        self.assertRejected(amount=Decimal("-1.00"))

    def test_adjusted_sale_cannot_be_deleted(self):
        self.adjust()
        with self.assertRaises(ProtectedError):
            self.sale.delete()


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

class PricingParityTest(TestCase):
    """WBS 3.3.4 y 3.4.5 — calcular_total() contra los casos compartidos con pricing.js (autor: Jesús)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(settings.BASE_DIR / "tests_fixtures" / "pricing_cases.json", encoding="utf-8") as fixture:
            cls.cases = json.load(fixture)

    def test_every_shared_case_gives_its_total(self):
        for case in self.cases["casos"]:
            with self.subTest(case["nombre"]):
                self.assertEqual(calcular_total(case["pedido"]), case["total_esperado_centavos"])

    def test_every_malformed_order_is_rejected(self):
        for case in self.cases["invalidos"]:
            with self.subTest(case["nombre"]), self.assertRaises(ValueError):
                calcular_total(case["pedido"])

    def test_result_is_an_int_in_cents(self):
        total = calcular_total({"lineas": [{"platillo_id": 1, "precio_base_centavos": 8500, "cantidad": 2}]})
        self.assertIs(type(total), int)
        self.assertEqual(total, 17000)

    def test_true_is_not_a_quantity(self):
        with self.assertRaises(ValueError):
            calcular_total({"lineas": [{"platillo_id": 1, "precio_base_centavos": 8500, "cantidad": True}]})


class CashSessionServiceTests(PosModelsBase):
    """WBS 3.5.1 — apertura y cierre del turno de caja (reglas 5, 12 y 13)."""

    def setUp(self):
        super().setUp()
        self.admin = get_user_model().objects.create_user(username="dueno", password="x-9Lq!pr2", role="admin")

    def sale(self, session, total, method="cash", **adjustment):
        sale = self.make_sale(session=session, charged_total=Decimal(total), server_total=Decimal(total),
                              payment_method=method)
        if adjustment:
            data = dict(sale=sale, kind=AdjustmentKind.ADJUSTMENT, authorized_by=self.admin)
            data.update(adjustment)
            SaleAdjustment.objects.create(**data)
        return sale

    def test_admin_opens_the_session_in_their_name(self):
        session = cash.open_session(self.admin, Decimal("500.00"))
        self.assertEqual((session.opened_by, session.status, session.opening_amount),
                         (self.admin, "open", Decimal("500.00")))
        self.assertEqual(session.business_date, timezone.localdate())
        self.assertEqual(cash.current_session(), session)

    def test_cashier_cannot_open_or_close(self):
        with self.assertRaises(cash.NotAdminError):
            cash.open_session(self.user, Decimal("500.00"))
        cash.open_session(self.admin, Decimal("500.00"))
        with self.assertRaises(cash.NotAdminError):
            cash.close_session(self.user, Decimal("500.00"))

    def test_inactive_admin_cannot_open(self):
        self.admin.is_active = False
        self.admin.save()
        with self.assertRaises(cash.NotAdminError):
            cash.open_session(self.admin, Decimal("500.00"))

    def test_only_one_open_session(self):
        cash.open_session(self.admin, Decimal("500.00"), business_date=date(2026, 11, 2))
        with self.assertRaises(cash.SessionAlreadyOpenError):
            cash.open_session(self.admin, Decimal("500.00"), business_date=date(2026, 11, 3))

    def test_only_one_session_per_day(self):
        cash.open_session(self.admin, Decimal("500.00"))
        cash.close_session(self.admin, Decimal("500.00"))
        with self.assertRaises(cash.DayAlreadyHasSessionError):
            cash.open_session(self.admin, Decimal("300.00"))

    def test_invalid_opening_amounts(self):
        for amount in ["-1", "10.001", "abc", "NaN"]:
            with self.subTest(amount=amount), self.assertRaises(cash.InvalidAmountError):
                cash.open_session(self.admin, amount)
        self.assertIsNone(cash.current_session())

    def test_offline_opening_keeps_its_uuid_and_device_time(self):
        uuid = uuid4()
        device_time = timezone.make_aware(datetime(2026, 11, 2, 7, 30))
        session = cash.open_session(self.admin, Decimal("400.00"), uuid=uuid, device_timestamp=device_time)
        self.assertEqual((session.uuid, session.device_timestamp, session.business_date),
                         (uuid, device_time, date(2026, 11, 2)))

    def test_repeated_uuid_is_discarded(self):
        uuid = uuid4()
        first = cash.open_session(self.admin, Decimal("400.00"), uuid=uuid)
        with self.assertRaises(cash.DuplicateOperationError) as error:
            cash.open_session(self.admin, Decimal("400.00"), uuid=uuid)
        self.assertEqual(error.exception.session, first)
        self.assertEqual(CashRegisterSession.objects.count(), 1)

    def test_require_open_session(self):
        with self.assertRaises(cash.NoOpenSessionError):
            cash.require_open_session()
        session = cash.open_session(self.admin, Decimal("500.00"))
        self.assertEqual(cash.require_open_session(), session)

    def test_totals_by_method_net_of_reversions(self):
        session = cash.open_session(self.admin, Decimal("500.00"))
        self.sale(session, "100.00")
        self.sale(session, "80.00", method="transfer")
        sold = self.sale(session, "60.00")
        item = OrderItem.objects.create(order=sold.order, dish=self.dish, quantity=2, unit_price=Decimal("30.00"))
        SaleAdjustment.objects.create(sale=sold, kind=AdjustmentKind.ADJUSTMENT, reason=AdjustmentReason.RETURN,
                                      order_item=item, quantity=1, amount=Decimal("30.00"), authorized_by=self.admin)
        self.sale(session, "45.00", reason=AdjustmentReason.PAYMENT_CORRECTION, new_payment_method="transfer")
        self.sale(session, "20.00", kind=AdjustmentKind.CANCELLATION, reason=AdjustmentReason.CAPTURE_ERROR,
                  amount=Decimal("20.00"))
        self.assertEqual(cash.sales_totals(session), {"cash": Decimal("130.00"), "transfer": Decimal("125.00")})
        self.assertEqual(cash.expected_cash(session), Decimal("630.00"))

    def test_close_records_the_difference_without_blocking(self):
        session = cash.open_session(self.admin, Decimal("500.00"))
        self.sale(session, "100.00")
        closed = cash.close_session(self.admin, Decimal("590.00"))
        self.assertEqual((closed.status, closed.closed_by), ("closed", self.admin))
        self.assertEqual((closed.expected_amount, closed.closing_amount, closed.cash_difference),
                         (Decimal("600.00"), Decimal("590.00"), Decimal("-10.00")))
        self.assertIsNone(cash.current_session())

    def test_close_is_refused_with_unsynced_sales(self):
        cash.open_session(self.admin, Decimal("500.00"))
        with self.assertRaises(cash.PendingSalesError) as error:
            cash.close_session(self.admin, Decimal("500.00"), pending_sales=3)
        self.assertEqual(str(error.exception), "No se puede cerrar la caja: faltan 3 ventas por sincronizar.")
        self.assertIsNotNone(cash.current_session())

    def test_close_without_open_session(self):
        with self.assertRaises(cash.NoOpenSessionError):
            cash.close_session(self.admin, Decimal("500.00"))
