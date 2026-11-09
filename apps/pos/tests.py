"""Unit tests for apps.pos. Whoever implements a service writes its tests."""

import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Category, Dish, Ingredient, Recipe, Units
from apps.inventory.models import MovementKind, StockMovement
from apps.pos import services as sales
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


class SaleServiceTests(TestCase):
    """WBS 3.3.5 y 3.3.8 — confirmar, cancelar y ajustar una venta (reglas 1, 2, 7 a 12 y 14)."""

    def setUp(self):
        users = get_user_model().objects
        self.admin = users.create_user(username="dueno", password="x-9Lq!pr2", role="admin")
        self.cashier = users.create_user(username="caja", password="x-9Lq!pr3", role="cashier")
        category = Category.objects.create(name="Burritos")
        self.burrito = Dish.objects.create(name="Burrito de asada", category=category, price=Decimal("85.00"))
        self.soda = Dish.objects.create(name="Refresco", category=category, price=Decimal("25.00"))
        self.tortilla = Ingredient.objects.create(name="Tortilla", unit=Units.PIECE, stock=Decimal("10"))
        self.beef = Ingredient.objects.create(name="Asada", unit=Units.G, stock=Decimal("1000"))
        self.onion = Ingredient.objects.create(name="Cebolla", unit=Units.G, stock=Decimal("200"))
        self.cheese = Ingredient.objects.create(name="Queso", unit=Units.G, stock=Decimal("100"))
        self.can = Ingredient.objects.create(name="Lata", unit=Units.PIECE, stock=Decimal("5"))
        for dish, ingredient, quantity in [(self.burrito, self.tortilla, "1"), (self.burrito, self.beef, "150"),
                                           (self.burrito, self.onion, "20"), (self.soda, self.can, "1")]:
            Recipe.objects.create(dish=dish, ingredient=ingredient, quantity=Decimal(quantity))
        Modifier.objects.create(dish=self.burrito, ingredient=self.cheese, kind="add",
                                price_adjustment=Decimal("15.00"), quantity=Decimal("30"))
        Modifier.objects.create(dish=self.burrito, ingredient=self.onion, kind="remove")
        self.session = cash.open_session(self.admin, Decimal("500.00"))

    def stock(self, ingredient):
        ingredient.refresh_from_db()
        return ingredient.stock

    def order(self, burritos=2, extra_cheese=True, no_onion=False, sodas=0, burrito_price=8500):
        modifiers = []
        if extra_cheese:
            modifiers.append({"tipo": "agregar", "insumo_id": self.cheese.pk, "ajuste_centavos": 1500})
        if no_onion:
            modifiers.append({"tipo": "quitar", "insumo_id": self.onion.pk})
        lines = [{"platillo_id": self.burrito.pk, "precio_base_centavos": burrito_price, "cantidad": burritos,
                  "modificadores": modifiers}]
        if sodas:
            lines.append({"platillo_id": self.soda.pk, "precio_base_centavos": 2500, "cantidad": sodas})
        return {"lineas": lines}

    def sell(self, pedido=None, total=20000, method="efectivo", user=None, **kwargs):
        return sales.confirm_sale(user or self.cashier, pedido or self.order(), method, total, **kwargs)

    # ----- Confirmar -----
    def test_online_sale_records_what_was_charged_and_deducts_inventory(self):
        sale = self.sell(self.order(no_onion=True))
        self.assertEqual((sale.charged_total, sale.server_total, sale.payment_method, sale.cash_session),
                         (Decimal("200.00"), Decimal("200.00"), "cash", self.session))
        self.assertEqual((sale.created_by, sale.needs_review, sale.review_reasons), (self.cashier, False, []))
        item = sale.order.items.get()
        self.assertEqual((item.dish, item.quantity, item.unit_price), (self.burrito, 2, Decimal("85.00")))
        self.assertEqual(sorted((m.kind, m.price_adjustment) for m in item.modifiers.all()),
                         [("add", Decimal("15.00")), ("remove", Decimal("0.00"))])
        self.assertEqual(self.stock(self.beef), Decimal("700"))
        self.assertEqual(self.stock(self.cheese), Decimal("40"))  # extra: 30 g x 2 (rule 2)
        self.assertEqual(self.stock(self.onion), Decimal("200"))  # removed: not deducted (rule 2)

    def test_needs_an_open_session_and_checks_it_before_pricing(self):
        cash.close_session(self.admin, Decimal("500.00"))
        with self.assertRaises(cash.NoOpenSessionError):
            self.sell(pedido={"lineas": "mal formado"})
        self.assertFalse(Sale.objects.exists())

    def test_offline_sale_keeps_its_uuid_and_device_time_and_is_applied_once(self):
        uuid, when = uuid4(), timezone.now() - timedelta(hours=2)
        sale = self.sell(uuid=uuid, session_uuid=self.session.uuid, device_timestamp=when)
        self.assertEqual((sale.uuid, sale.device_timestamp), (uuid, when))
        with self.assertRaises(sales.DuplicateSaleError) as raised:
            self.sell(uuid=uuid, session_uuid=self.session.uuid, device_timestamp=when)
        self.assertEqual(raised.exception.sale, sale)
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(self.stock(self.beef), Decimal("700"))

    def test_quarantine_reasons(self):
        closed = CashRegisterSession.objects.create(
            business_date=date(2026, 1, 2), opened_by=self.admin, opening_amount=Decimal("0"),
            status="closed", device_timestamp=timezone.now())
        unknown_dish = {"lineas": [{"platillo_id": 999, "precio_base_centavos": 100, "cantidad": 1}]}
        unknown_modifier = {"lineas": [{"platillo_id": self.soda.pk, "precio_base_centavos": 2500, "cantidad": 1,
                                        "modificadores": [{"tipo": "agregar", "insumo_id": self.cheese.pk,
                                                           "ajuste_centavos": 0}]}]}
        cases = [
            (dict(session_uuid=closed.uuid), "turno_invalido"),
            (dict(session_uuid=uuid4()), "turno_invalido"),
            (dict(pedido=unknown_dish, total=100), "platillo_desconocido"),
            (dict(pedido=unknown_modifier, total=2500), "platillo_desconocido"),
            (dict(total=19999), "total_inconsistente"),
        ]
        for kwargs, reason in cases:
            with self.subTest(reason=reason, kwargs=kwargs), self.assertRaises(sales.SaleError) as raised:
                self.sell(uuid=uuid4(), **kwargs)
            self.assertEqual(raised.exception.quarantine_reason, reason)
        self.assertFalse(Sale.objects.exists())
        self.assertFalse(StockMovement.objects.exists())

    def test_user_without_permission(self):
        self.cashier.is_active = False
        self.cashier.save()
        with self.assertRaises(sales.UserWithoutPermissionError) as raised:
            self.sell()
        self.assertEqual(raised.exception.quarantine_reason, "usuario_sin_permiso")

    def test_missing_recipe_goes_to_quarantine_or_applies_without_deduction(self):
        Recipe.objects.filter(dish=self.soda).delete()
        pedido = {"lineas": [{"platillo_id": self.soda.pk, "precio_base_centavos": 2500, "cantidad": 1}]}
        with self.assertRaises(sales.MissingRecipeError) as raised:
            self.sell(pedido, total=2500)
        self.assertEqual(raised.exception.quarantine_reason, "receta_faltante")
        sale = self.sell(pedido, total=2500, deduct_inventory=False)
        self.assertEqual(sale.charged_total, Decimal("25.00"))
        self.assertFalse(StockMovement.objects.exists())

    def test_malformed_order_or_payment_method(self):
        for kwargs in [dict(method="tarjeta"), dict(pedido={"lineas": []}, total=0),
                       dict(pedido={"lineas": [{"precio_base_centavos": 1, "cantidad": 1}]}, total=1),
                       dict(total=Decimal("200.00"))]:
            with self.subTest(kwargs=kwargs), self.assertRaises(sales.InvalidOrderError):
                self.sell(**kwargs)

    def test_what_was_charged_wins_over_the_current_catalog(self):
        self.burrito.price = Decimal("90.00")
        self.burrito.save()
        sale = self.sell(uuid=uuid4(), session_uuid=self.session.uuid)
        self.assertEqual((sale.charged_total, sale.server_total), (Decimal("200.00"), Decimal("210.00")))
        self.assertEqual((sale.needs_review, sale.review_reasons), (True, ["precio_distinto"]))

    def test_negative_stock_is_kept_and_marked_for_review(self):
        sale = self.sell(self.order(burritos=1, extra_cheese=False, sodas=6), total=8500 + 6 * 2500)
        self.assertEqual(self.stock(self.can), Decimal("-1"))
        self.assertEqual((sale.needs_review, sale.review_reasons), (True, ["existencia_negativa"]))

    # ----- Cancelar -----
    def test_cancel_for_capture_error_gives_money_and_inventory_back(self):
        sale = self.sell()
        adjustment = sales.cancel_sale(self.admin, sale, "error_captura", "Se marcó dos veces")
        self.assertEqual((adjustment.kind, adjustment.amount, adjustment.authorized_by),
                         ("cancellation", Decimal("200.00"), self.admin))
        self.assertEqual((self.stock(self.beef), self.stock(self.cheese)), (Decimal("1000"), Decimal("100")))
        self.assertEqual(cash.sales_totals(self.session)["cash"], Decimal("0.00"))
        self.assertEqual(Sale.objects.get(pk=sale.pk).charged_total, Decimal("200.00"))  # immutable (rule 7)

    def test_cancel_for_return_records_waste_and_keeps_stock(self):
        sale = self.sell()
        sales.cancel_sale(self.admin, sale, "devolucion")
        self.assertEqual(self.stock(self.beef), Decimal("700"))
        waste = StockMovement.objects.get(ingredient=self.beef, kind=MovementKind.WASTE)
        self.assertEqual((waste.quantity, waste.sale_uuid, waste.note), (Decimal("-300"), sale.uuid, "Devolución"))
        self.assertEqual(cash.sales_totals(self.session)["cash"], Decimal("0.00"))

    def test_cancel_needs_an_admin_a_valid_reason_and_happens_once(self):
        sale = self.sell()
        with self.assertRaises(sales.NotAdminError):
            sales.cancel_sale(self.cashier, sale, "error_captura")
        with self.assertRaises(sales.AdjustmentError):
            sales.cancel_sale(self.admin, sale, "correccion_pago")
        sales.cancel_sale(self.admin, sale, "error_captura")
        with self.assertRaises(sales.AdjustmentError):
            sales.cancel_sale(self.admin, sale, "error_captura")
        with self.assertRaises(sales.AdjustmentError):
            sales.adjust_sale(self.admin, sale, "correccion_pago", new_payment_method="transferencia")

    def test_cancel_of_a_sale_applied_without_deduction_leaves_inventory_alone(self):
        sale = self.sell(deduct_inventory=False)
        sales.cancel_sale(self.admin, sale, "error_captura")
        self.assertFalse(StockMovement.objects.exists())

    def test_sale_of_a_closed_session_cannot_be_changed(self):
        sale = self.sell()
        cash.close_session(self.admin, Decimal("700.00"))
        with self.assertRaises(sales.AdjustmentError):
            sales.cancel_sale(self.admin, sale, "error_captura")

    # ----- Ajustar -----
    def test_adjust_units_of_a_line_and_then_cancel_the_rest(self):
        sale = self.sell()
        item = sale.order.items.get()
        adjustment = sales.adjust_sale(self.admin, sale, "error_captura", order_item=item, quantity=1)
        self.assertEqual((adjustment.amount, adjustment.quantity), (Decimal("100.00"), 1))  # 85 + 15 of cheese
        self.assertEqual((self.stock(self.beef), self.stock(self.cheese)), (Decimal("850"), Decimal("70")))
        with self.assertRaises(sales.AdjustmentError):
            sales.adjust_sale(self.admin, sale, "error_captura", order_item=item, quantity=2)
        cancellation = sales.cancel_sale(self.admin, sale, "error_captura")
        self.assertEqual(cancellation.amount, Decimal("100.00"))
        self.assertEqual(self.stock(self.beef), Decimal("1000"))
        self.assertEqual(cash.sales_totals(self.session)["cash"], Decimal("0.00"))

    def test_adjust_rejects_a_line_of_another_sale(self):
        sale, other = self.sell(), self.sell()
        with self.assertRaises(sales.AdjustmentError):
            sales.adjust_sale(self.admin, sale, "devolucion", order_item=other.order.items.get(), quantity=1)

    def test_payment_correction_only_moves_the_sale_to_the_other_method(self):
        sale = self.sell()
        adjustment = sales.adjust_sale(self.admin, sale, "correccion_pago", new_payment_method="transferencia")
        self.assertEqual((adjustment.amount, adjustment.new_payment_method), (Decimal("0.00"), "transfer"))
        self.assertEqual(cash.sales_totals(self.session), {"cash": Decimal("0.00"), "transfer": Decimal("200.00")})
        self.assertEqual(self.stock(self.beef), Decimal("700"))
        with self.assertRaises(sales.AdjustmentError):
            sales.adjust_sale(self.admin, sale, "correccion_pago", new_payment_method="transfer")
