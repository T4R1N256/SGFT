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
from django.test import Client, TestCase
from django.utils import timezone

from apps.catalog.models import Category, Dish, Ingredient, Recipe, Units
from apps.inventory.models import MovementKind, StockMovement
from apps.pos import services as sales
from apps.pos import services_cash_session as cash
from apps.pos.services_pricing import calcular_total
from apps.pos.models import (
    AdjustmentKind, AdjustmentReason, CashRegisterSession, Modifier, Order, OrderItem, QuarantinedOperation,
    QuarantineReason, QuarantineResolution, QuarantineStatus, ReviewReason, Sale, SaleAdjustment,
    validate_review_reasons,
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

class QuarantineBase(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.admin = users.create_user(username="dueno", password="x-9Lq!pr2", role="admin")
        self.cashier = users.create_user(username="caja", password="x-9Lq!pr3", role="cashier")
        category = Category.objects.create(name="Burritos")
        self.burrito = Dish.objects.create(name="Burrito de asada", category=category, price=Decimal("85.00"))
        self.beef = Ingredient.objects.create(name="Asada", unit=Units.G, stock=Decimal("1000"))
        self.cheese = Ingredient.objects.create(name="Queso", unit=Units.G, stock=Decimal("500"))
        Recipe.objects.create(dish=self.burrito, ingredient=self.beef, quantity=Decimal("150"))
        Modifier.objects.create(dish=self.burrito, ingredient=self.cheese, kind="add",
                                price_adjustment=Decimal("15.00"), quantity=Decimal("30"))
        self.session = cash.open_session(self.admin, Decimal("500.00"))

    def quarantine(self, reason=QuarantineReason.MISSING_RECIPE, base=8500, total=20000, user=None, turno=None,
                   **extra):
        payload = {"uuid": str(uuid4()), "tipo": "venta", "turno_uuid": str(turno or self.session.uuid),
                   "metodo_pago": "efectivo", "total_cobrado_centavos": total, "pedido": {"lineas": [
                       {"platillo_id": self.burrito.pk, "precio_base_centavos": base, "cantidad": 2,
                        "modificadores": [{"tipo": "agregar", "insumo_id": self.cheese.pk, "ajuste_centavos": 1500}]}
                   ]}, **extra}
        operation = QuarantinedOperation.objects.create(
            uuid=payload["uuid"], operation_type=payload["tipo"], payload=payload, reason=reason,
            user=user or self.cashier, device_timestamp=timezone.now() - timedelta(hours=1))
        operation.refresh_from_db()
        return operation

    def stock(self, ingredient):
        ingredient.refresh_from_db()
        return ingredient.stock



class QuarantineResolutionTests(QuarantineBase):
    """WBS 3.4.9 — resolver la cuarentena con sus tres salidas y revisar ventas marcadas (reglas 9, 10 y 14)."""

    def resolve(self, operation, resolution, admin=None):
        return sales.resolve_quarantine(admin or self.admin, operation, resolution)

    def test_apply_records_the_sale_with_its_uuid_and_deducts_inventory(self):
        operation = self.quarantine()
        resolved = self.resolve(operation, QuarantineResolution.APPLY)
        sale = resolved.sale
        self.assertEqual((sale.uuid, sale.device_timestamp, sale.created_by, sale.cash_session),
                         (operation.uuid, operation.device_timestamp, self.cashier, self.session))
        self.assertEqual((sale.charged_total, sale.needs_review), (Decimal("200.00"), False))
        self.assertEqual((resolved.status, resolved.resolution, resolved.resolved_by),
                         (QuarantineStatus.RESOLVED, "apply", self.admin))
        self.assertIsNotNone(resolved.resolved_at)
        self.assertEqual(self.stock(self.beef), Decimal("700"))
        self.assertEqual(self.stock(self.cheese), Decimal("440"))

    def test_apply_uses_the_current_catalog_and_keeps_what_was_charged(self):
        # The order did not match its own total (8000 x 2 + extras = 19000, charged 20000).
        operation = self.quarantine(QuarantineReason.INCONSISTENT_TOTAL, base=8000)
        sale = self.resolve(operation, QuarantineResolution.APPLY).sale
        self.assertEqual(sale.order.items.get().unit_price, Decimal("85.00"))
        self.assertEqual((sale.charged_total, sale.server_total, sale.needs_review),
                         (Decimal("200.00"), Decimal("200.00"), False))

        self.burrito.price = Decimal("90.00")
        self.burrito.save()
        sale = self.resolve(self.quarantine(QuarantineReason.INCONSISTENT_TOTAL, base=8000),
                            QuarantineResolution.APPLY).sale
        self.assertEqual((sale.charged_total, sale.server_total, sale.review_reasons),
                         (Decimal("200.00"), Decimal("210.00"), ["precio_distinto"]))

    def test_apply_without_deduction_skips_the_missing_recipe(self):
        Recipe.objects.all().delete()
        operation = self.quarantine()
        with self.assertRaisesMessage(sales.ResolutionError, "sin descontar inventario"):
            self.resolve(operation, QuarantineResolution.APPLY)
        sale = self.resolve(operation, QuarantineResolution.APPLY_NO_DEDUCTION).sale
        self.assertEqual(sale.charged_total, Decimal("200.00"))
        self.assertEqual((self.stock(self.beef), self.stock(self.cheese)), (Decimal("1000"), Decimal("500")))
        self.assertFalse(StockMovement.objects.exists())

    def test_discard_records_nothing(self):
        operation = self.resolve(self.quarantine(QuarantineReason.UNKNOWN_DISH), QuarantineResolution.DISCARD)
        self.assertEqual((operation.status, operation.resolution, operation.sale), ("resolved", "discard", None))
        self.assertFalse(Sale.objects.exists())

    def test_a_failed_resolution_changes_nothing(self):
        operation = self.quarantine(QuarantineReason.UNKNOWN_DISH)
        operation.payload["pedido"]["lineas"][0]["platillo_id"] = 999
        operation.save()
        with self.assertRaisesMessage(sales.ResolutionError, "descártala"):
            self.resolve(operation, QuarantineResolution.APPLY)
        operation.refresh_from_db()
        self.assertEqual((operation.status, operation.resolution), (QuarantineStatus.PENDING, ""))
        self.assertFalse(Sale.objects.exists())
        self.assertEqual(self.stock(self.beef), Decimal("1000"))

    def test_only_an_active_admin_resolves_and_only_once(self):
        operation = self.quarantine()
        with self.assertRaisesMessage(sales.ResolutionError, "Solo un Administrador"):
            self.resolve(operation, QuarantineResolution.DISCARD, admin=self.cashier)
        self.resolve(operation, QuarantineResolution.DISCARD)
        with self.assertRaisesMessage(sales.ResolutionError, "ya se resolvió"):
            self.resolve(operation, QuarantineResolution.APPLY)

    def test_a_user_without_permission_leaves_the_sale_in_the_admins_name(self):
        self.cashier.is_active = False
        self.cashier.save()
        sale = self.resolve(self.quarantine(QuarantineReason.USER_WITHOUT_PERMISSION),
                            QuarantineResolution.APPLY).sale
        self.assertEqual(sale.created_by, self.admin)

    def test_a_sale_of_an_unknown_session_goes_to_the_open_one(self):
        sale = self.resolve(self.quarantine(QuarantineReason.INVALID_SESSION, turno=uuid4()),
                            QuarantineResolution.APPLY).sale
        self.assertEqual(sale.cash_session, self.session)

    def test_a_sale_of_a_closed_session_or_without_an_open_one_is_refused(self):
        operation = self.quarantine(QuarantineReason.INVALID_SESSION)
        unknown = self.quarantine(QuarantineReason.INVALID_SESSION, turno=uuid4())
        cash.close_session(self.admin, Decimal("500.00"))
        with self.assertRaisesMessage(sales.ResolutionError, "ya se cerró"):
            self.resolve(operation, QuarantineResolution.APPLY)
        with self.assertRaisesMessage(sales.ResolutionError, "abre la caja"):
            self.resolve(unknown, QuarantineResolution.APPLY)

    def test_a_quarantined_opening_is_applied_with_its_uuid(self):
        cash.close_session(self.admin, Decimal("500.00"))
        when = timezone.now() + timedelta(days=1)
        operation = QuarantinedOperation.objects.create(
            uuid=uuid4(), operation_type="apertura_turno", reason=QuarantineReason.USER_WITHOUT_PERMISSION,
            payload={"tipo": "apertura_turno", "efectivo_inicial_centavos": 30000}, user=self.cashier,
            device_timestamp=when)
        with self.assertRaisesMessage(sales.ResolutionError, "no descuenta inventario"):
            self.resolve(operation, QuarantineResolution.APPLY_NO_DEDUCTION)
        session = self.resolve(operation, QuarantineResolution.APPLY).cash_session
        self.assertEqual((session.uuid, session.opened_by, session.opening_amount),
                         (operation.uuid, self.admin, Decimal("300.00")))

    def test_a_repeated_opening_must_be_discarded(self):
        operation = QuarantinedOperation.objects.create(
            uuid=uuid4(), operation_type="apertura_turno", reason=QuarantineReason.SESSION_ALREADY_OPEN,
            payload={"tipo": "apertura_turno", "efectivo_inicial_centavos": 50000}, user=self.admin,
            device_timestamp=timezone.now())
        with self.assertRaisesMessage(sales.ResolutionError, "Descártala"):
            self.resolve(operation, QuarantineResolution.APPLY)

    def test_mark_sale_reviewed(self):
        self.burrito.price = Decimal("90.00")
        self.burrito.save()
        sale = sales.confirm_sale(self.cashier, self.quarantine().payload["pedido"], "efectivo", 20000)
        self.assertTrue(sale.needs_review)
        with self.assertRaisesMessage(sales.ResolutionError, "Solo un Administrador"):
            sales.mark_sale_reviewed(self.cashier, sale)
        sale = sales.mark_sale_reviewed(self.admin, sale)
        self.assertEqual((sale.reviewed_by, sale.needs_review, sale.charged_total),
                         (self.admin, True, Decimal("200.00")))
        with self.assertRaisesMessage(sales.ResolutionError, "no está pendiente"):
            sales.mark_sale_reviewed(self.admin, sale)


class SalesAdminTests(QuarantineBase):
    """WBS 3.4.9 — la bandeja en Django Admin: acciones de la cuarentena y de las ventas por revisar."""

    def setUp(self):
        super().setUp()
        self.admin.is_staff = self.admin.is_superuser = True
        self.admin.save()
        self.client.force_login(self.admin)

    def url(self, name, *args):
        from django.urls import reverse  # local: the module's imports are shared with the sync tests
        return reverse(f"admin:pos_{name}", args=args)

    def act(self, model, action, *objects):
        return self.client.post(self.url(f"{model}_changelist"), {
            "action": action, "_selected_action": [obj.pk for obj in objects]}, follow=True)

    def test_quarantine_actions(self):
        applied, discarded = self.quarantine(), self.quarantine()
        response = self.act("quarantinedoperation", "resolve_apply", applied)
        self.assertContains(response, "1 operación(es) resuelta(s)")
        self.act("quarantinedoperation", "resolve_discard", discarded)
        applied.refresh_from_db()
        discarded.refresh_from_db()
        self.assertEqual((applied.resolution, discarded.resolution), ("apply", "discard"))
        self.assertEqual(Sale.objects.get().uuid, applied.uuid)

    def test_quarantine_action_reports_what_failed(self):
        Recipe.objects.all().delete()
        operation = self.quarantine()
        response = self.act("quarantinedoperation", "resolve_apply", operation)
        self.assertContains(response, "Agrega la receta")
        self.act("quarantinedoperation", "resolve_apply_no_deduction", operation)
        operation.refresh_from_db()
        self.assertEqual(operation.resolution, "apply_no_deduction")

    def test_admin_is_read_only_and_shows_the_original_content(self):
        operation = self.quarantine()
        page = self.client.get(self.url("quarantinedoperation_change", operation.pk))
        self.assertContains(page, "total_cobrado_centavos")
        self.assertNotContains(page, 'name="_save"')
        self.assertEqual(self.client.get(self.url("quarantinedoperation_add")).status_code, 403)

    def test_sales_pending_review_and_mark_reviewed(self):
        self.burrito.price = Decimal("90.00")
        self.burrito.save()
        marked = sales.confirm_sale(self.cashier, self.quarantine().payload["pedido"], "efectivo", 20000)
        url = self.url("sale_changelist")
        self.assertContains(self.client.get(url, {"revision": "pendiente"}), "precio_distinto")
        response = self.act("sale", "mark_reviewed", marked)
        self.assertContains(response, "1 venta(s) marcada(s) como revisada(s).")
        self.assertNotContains(self.client.get(url, {"revision": "pendiente"}), "precio_distinto")


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


class SyncOperationsTests(TestCase):
    """WBS 3.4.6 — POST /pos/sync/, contrato v1 §6 (reglas 1, 8, 9, 10, 12 y 14)."""

    def setUp(self):
        users = get_user_model().objects
        self.admin = users.create_user(username="dueno", password="x-9Lq!pr2", role="admin")
        self.cashier = users.create_user(username="caja", password="x-9Lq!pr3", role="cashier")
        category = Category.objects.create(name="Burritos")
        self.burrito = Dish.objects.create(name="Burrito de asada", category=category, price=Decimal("85.00"))
        self.beef = Ingredient.objects.create(name="Asada", unit=Units.G, stock=Decimal("1000"))
        Recipe.objects.create(dish=self.burrito, ingredient=self.beef, quantity=Decimal("150"))
        self.client.force_login(self.cashier)
        self.url = "/pos/sync/"

    def opening(self, uuid=None, user=None, minute=0):
        return {"uuid": str(uuid or uuid4()), "tipo": "apertura_turno", "usuario_id": (user or self.admin).pk,
                "marca_tiempo_dispositivo": f"2026-11-04T08:{minute:02d}:00-07:00", "efectivo_inicial_centavos": 50000}

    def sale(self, session_uuid, uuid=None, burritos=2, total=None, minute=15, user=None):
        return {"uuid": str(uuid or uuid4()), "tipo": "venta", "usuario_id": (user or self.cashier).pk,
                "marca_tiempo_dispositivo": f"2026-11-04T09:{minute:02d}:00-07:00", "turno_uuid": str(session_uuid),
                "metodo_pago": "efectivo", "total_cobrado_centavos": 8500 * burritos if total is None else total,
                "pedido": {"lineas": [{"platillo_id": self.burrito.pk, "precio_base_centavos": 8500,
                                       "cantidad": burritos}]}}

    def send(self, *operations, version=1):
        return self.client.post(self.url, json.dumps({"version_contrato": version, "operaciones": list(operations)}),
                                content_type="application/json")

    def states(self, response):
        self.assertEqual(response.status_code, 200)
        return [(r["estado"], r.get("motivo") or r.get("motivos")) for r in response.json()["resultados"]]

    def test_opening_and_its_sales_in_any_order(self):
        opening = self.opening()
        response = self.send(self.sale(opening["uuid"], minute=30), self.sale(opening["uuid"]), opening)
        self.assertEqual(self.states(response), [("aplicada", None)] * 3)
        session = CashRegisterSession.objects.get(uuid=opening["uuid"])
        self.assertEqual((session.opened_by, session.opening_amount), (self.admin, Decimal("500.00")))
        self.assertEqual(Sale.objects.filter(cash_session=session).count(), 2)
        self.beef.refresh_from_db()
        self.assertEqual(self.beef.stock, Decimal("400"))

    def test_the_same_batch_twice_applies_once(self):
        opening = self.opening()
        batch = [opening, self.sale(opening["uuid"])]
        self.send(*batch)
        self.assertEqual(self.states(self.send(*batch)), [("duplicada", None)] * 2)
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(StockMovement.objects.filter(kind=MovementKind.SALE).count(), 1)

    def test_a_uuid_already_used_in_another_table_is_a_duplicate(self):
        opening = self.opening()
        self.send(opening)
        clash = self.sale(opening["uuid"], uuid=opening["uuid"])
        self.assertEqual(self.states(self.send(clash)), [("duplicada", None)])
        self.assertFalse(Sale.objects.exists())

    def test_quarantine_reasons(self):
        opening = self.opening()
        self.send(opening)
        unknown = self.sale(opening["uuid"])
        unknown["pedido"]["lineas"][0]["platillo_id"] = 999
        no_recipe_dish = Dish.objects.create(name="Agua", category=self.burrito.category, price=Decimal("20.00"))
        no_recipe = self.sale(opening["uuid"])
        no_recipe["pedido"]["lineas"][0]["platillo_id"] = no_recipe_dish.pk
        malformed = self.sale(opening["uuid"])
        malformed["pedido"] = {"lineas": "x"}
        inactive = get_user_model().objects.create_user(username="ex", password="x-9Lq!pr4", role="cashier",
                                                        is_active=False)
        response = self.send(
            self.opening(user=self.cashier, minute=1), self.opening(minute=2), self.sale(uuid4()), unknown, no_recipe,
            self.sale(opening["uuid"], total=1), malformed, self.sale(opening["uuid"], user=inactive),
        )
        self.assertEqual(self.states(response), [
            ("cuarentena", "usuario_sin_permiso"), ("cuarentena", "turno_ya_abierto"),
            ("cuarentena", "turno_invalido"), ("cuarentena", "platillo_desconocido"),
            ("cuarentena", "receta_faltante"), ("cuarentena", "total_inconsistente"),
            ("cuarentena", "total_inconsistente"), ("cuarentena", "usuario_sin_permiso"),
        ])
        self.assertEqual(QuarantinedOperation.objects.count(), 8)
        self.assertEqual(QuarantinedOperation.objects.get(uuid=unknown["uuid"]).payload, unknown)
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(self.states(self.send(unknown)), [("duplicada", None)])

    def test_review_reasons(self):
        opening = self.opening()
        self.send(opening)
        self.burrito.price = Decimal("90.00")
        self.burrito.save()
        response = self.send(self.sale(opening["uuid"], burritos=7))  # 1050 g of 1000
        self.assertEqual(self.states(response), [("aplicada_con_revision", ["precio_distinto", "existencia_negativa"])])
        self.assertEqual(Sale.objects.get().charged_total, Decimal("595.00"))  # what was charged wins

    def test_one_failure_does_not_revert_the_others(self):
        opening = self.opening()
        response = self.send(opening, self.sale(opening["uuid"], total=1), self.sale(opening["uuid"], minute=20))
        self.assertEqual([s for s, _ in self.states(response)], ["aplicada", "cuarentena", "aplicada"])
        self.assertEqual(Sale.objects.count(), 1)

    def test_whole_batch_errors_apply_nothing(self):
        opening = self.opening()
        self.client.logout()
        self.assertEqual(self.send(opening).status_code, 401)
        self.client.force_login(self.cashier)
        self.assertEqual(self.send(opening, version=2).status_code, 400)
        self.assertEqual(self.client.post(self.url, "{", content_type="application/json").status_code, 400)
        bad_time = {**self.opening(), "marca_tiempo_dispositivo": "ayer"}
        self.assertEqual(self.send(opening, bad_time).status_code, 400)
        self.assertEqual(self.send(*[self.opening() for _ in range(101)]).status_code, 413)
        self.assertFalse(CashRegisterSession.objects.exists())

    def test_needs_the_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.cashier)
        response = client.post(self.url, json.dumps({"version_contrato": 1, "operaciones": []}),
                               content_type="application/json")
        self.assertEqual(response.status_code, 403)


class SyncEdgeCaseTests(TestCase):
    """WBS 3.3.6 — /pos/sync/: validación de cada operación y carreras de UUID (autor: Jared)."""

    setUp = SyncOperationsTests.setUp
    opening = SyncOperationsTests.opening
    sale = SyncOperationsTests.sale
    send = SyncOperationsTests.send
    states = SyncOperationsTests.states

    def test_a_malformed_operation_rejects_the_whole_batch(self):
        good = self.opening()
        cases = [
            ("no es objeto", "Cada operación debe ser un objeto."),
            ({**self.opening(), "uuid": "no-es-uuid"}, "Una operación no trae un uuid válido."),
            ({**self.opening(), "marca_tiempo_dispositivo": "2026-11-04T08:00:00"}, "con zona horaria"),
            ({**self.opening(), "usuario_id": str(self.admin.pk)}, "usuario_id debe ser un entero"),
            ({**self.opening(), "efectivo_inicial_centavos": -1}, "efectivo_inicial_centavos debe ser un entero"),
            ({**self.sale(uuid4()), "turno_uuid": "no-es-uuid"}, "turno_uuid no es un UUID"),
            ({**self.opening(), "tipo": "merma"}, "tipo debe ser «apertura_turno» o «venta»"),
        ]
        for operation, message in cases:
            with self.subTest(message=message):
                response = self.send(good, operation)
                self.assertEqual(response.status_code, 400)
                self.assertIn(message, response.json()["detalle"])
        self.assertFalse(CashRegisterSession.objects.exists())
        self.assertFalse(QuarantinedOperation.objects.exists())

    def test_an_operation_of_an_unknown_user_goes_to_quarantine(self):
        opening = {**self.opening(), "usuario_id": 999999}
        sale = {**self.sale(uuid4()), "usuario_id": 999999}
        self.assertEqual(self.states(self.send(opening, sale)),
                         [("cuarentena", "usuario_sin_permiso"), ("cuarentena", "usuario_sin_permiso")])
        self.assertEqual(QuarantinedOperation.objects.filter(user=None).count(), 2)

    def test_a_duplicate_caught_by_the_service_still_answers_duplicate(self):
        from unittest import mock
        opening = self.opening()
        sale = self.sale(opening["uuid"])
        self.send(opening, sale)
        with mock.patch("apps.pos.views_sync._already_known", return_value=False):
            self.assertEqual(self.states(self.send(opening, sale)), [("duplicada", None), ("duplicada", None)])
        self.assertEqual((CashRegisterSession.objects.count(), Sale.objects.count()), (1, 1))

    def test_two_requests_with_the_same_uuid(self):
        # Another request saves the same UUID between the check and the insert: the unique constraint fails.
        from unittest import mock
        opening = self.opening()
        with mock.patch("apps.pos.views_sync._apply_opening", side_effect=IntegrityError), \
                mock.patch("apps.pos.views_sync._already_known", side_effect=[False, True]):
            self.assertEqual(self.states(self.send(opening)), [("duplicada", None)])
        # If the UUID still is nowhere, the error is something else and must not be hidden.
        with mock.patch("apps.pos.views_sync._apply_opening", side_effect=IntegrityError), \
                mock.patch("apps.pos.views_sync._already_known", return_value=False), \
                self.assertRaises(IntegrityError):
            self.send(opening)


class SaleEdgeCaseTests(TestCase):
    """WBS 3.3.6 — pedidos mal formados y ajustes que no proceden (autor: Jared)."""

    setUp = SaleServiceTests.setUp
    order = SaleServiceTests.order
    sell = SaleServiceTests.sell

    def test_a_modifier_without_its_ingredient_is_a_malformed_order(self):
        pedido = {"lineas": [{"platillo_id": self.burrito.pk, "precio_base_centavos": 8500, "cantidad": 1,
                              "modificadores": [{"tipo": "agregar", "ajuste_centavos": 1500}]}]}
        with self.assertRaisesMessage(sales.InvalidOrderError, "Cada modificador debe traer insumo_id."):
            self.sell(pedido, total=10000)
        self.assertFalse(Sale.objects.exists())

    def test_adjustments_that_do_not_apply(self):
        sale = self.sell()
        item = sale.order.items.get()
        with self.assertRaisesMessage(sales.AdjustmentError, "Indica el nuevo método de pago"):
            sales.adjust_sale(self.admin, sale, "correccion_pago", new_payment_method="tarjeta")
        with self.assertRaisesMessage(sales.AdjustmentError, "El motivo debe ser"):
            sales.adjust_sale(self.admin, sale, "otro", order_item=item, quantity=1)
        sales.adjust_sale(self.admin, sale, "error_captura", order_item=item, quantity=2)
        with self.assertRaisesMessage(sales.AdjustmentError, "Esa línea ya se ajustó completa."):
            sales.adjust_sale(self.admin, sale, "error_captura", order_item=item, quantity=1)
        self.assertEqual(sale.adjustments.count(), 1)


class QuarantineEdgeCaseTests(QuarantineBase):
    """WBS 3.3.6 — resoluciones de cuarentena que no se pueden aplicar y la bandeja de ventas (autor: Jared)."""

    def resolve(self, operation, resolution=QuarantineResolution.APPLY):
        return sales.resolve_quarantine(self.admin, operation, resolution)

    def edit(self, operation, **changes):
        operation.payload = {**operation.payload, **changes}
        operation.save()
        return operation

    def test_a_sale_that_cannot_be_applied_says_why(self):
        duplicate = self.quarantine()
        sales.confirm_sale(self.cashier, duplicate.payload["pedido"], "efectivo", 20000, uuid=duplicate.uuid,
                           session_uuid=self.session.uuid, device_timestamp=duplicate.device_timestamp)
        cases = [
            (duplicate, "Ya hay una venta con este UUID"),
            (self.edit(self.quarantine(), pedido={"lineas": [
                {"platillo_id": 999999, "precio_base_centavos": 8500, "cantidad": 1}]}), "descártala"),
            (self.edit(self.quarantine(), pedido={"lineas": "no es lista"}), "no es válido"),
        ]
        for operation, message in cases:
            with self.subTest(message=message), self.assertRaisesMessage(sales.ResolutionError, message):
                self.resolve(operation)
            operation.refresh_from_db()
            self.assertEqual(operation.status, QuarantineStatus.PENDING)

    def test_an_opening_that_cannot_be_applied_says_why(self):
        cash.close_session(self.admin, Decimal("500.00"))

        def opening(uuid=None, cents=30000):
            return QuarantinedOperation.objects.create(
                uuid=uuid or uuid4(), operation_type="apertura_turno", reason=QuarantineReason.USER_WITHOUT_PERMISSION,
                payload={"tipo": "apertura_turno", "efectivo_inicial_centavos": cents}, user=self.admin,
                device_timestamp=timezone.now() + timedelta(days=1))

        with self.assertRaisesMessage(sales.ResolutionError, "no trae un efectivo inicial válido"):
            self.resolve(opening(cents=-5))
        with self.assertRaisesMessage(sales.ResolutionError, "Ya hay un turno con este UUID"):
            self.resolve(opening(uuid=self.session.uuid))

    def test_sales_admin_lists_reviewed_sales_with_their_lines(self):
        self.admin.is_staff = self.admin.is_superuser = True
        self.admin.save()
        self.client.force_login(self.admin)
        self.burrito.price = Decimal("90.00")
        self.burrito.save()
        sale = sales.mark_sale_reviewed(self.admin, sales.confirm_sale(
            self.cashier, self.quarantine().payload["pedido"], "efectivo", 20000))
        from django.urls import reverse  # local: the module's imports are shared with the sync tests
        changelist = self.client.get(reverse("admin:pos_sale_changelist"), {"revision": "revisada"})
        self.assertContains(changelist, "precio_distinto")
        change = self.client.get(reverse("admin:pos_sale_change", args=[sale.pk]))
        self.assertContains(change, "2 × Burrito de asada ($85.00)")  # what was charged (rule 14)


class PosModelTextTests(QuarantineBase):
    """WBS 3.3.6 — cómo se nombran los registros de pos en Django Admin (autor: Jared)."""

    def test_names(self):
        sale = sales.confirm_sale(self.cashier, self.quarantine().payload["pedido"], "efectivo", 20000)
        item = sale.order.items.get()
        modifier = Modifier.objects.get()
        line_modifier = item.modifiers.get()
        adjustment = sales.adjust_sale(self.admin, sale, "error_captura", order_item=item, quantity=1)
        self.assertEqual(str(sale.order), f"Pedido {sale.order.pk}")
        self.assertEqual(str(item), f"2 x {self.burrito.pk}")
        self.assertEqual(str(modifier), f"Agregar {self.cheese.pk} en {self.burrito.pk}")
        self.assertEqual(str(line_modifier), f"Agregar {self.cheese.pk}")
        self.assertEqual(str(adjustment), f"Ajuste de {sale.pk} (Error de captura)")
