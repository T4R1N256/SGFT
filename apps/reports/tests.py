"""Unit tests for apps.reports. Whoever implements a service writes its tests."""
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Category, Dish, Ingredient, Recipe, Units
from apps.inventory.services import register_waste
from apps.pos import services as sales
from apps.pos import services_cash_session as cash
from apps.reports import services as reports

DAY = date(2026, 11, 4)  # a Wednesday


def at(day, hour, minute=0):
    return timezone.make_aware(datetime(day.year, day.month, day.day, hour, minute))


class ReportServiceTests(TestCase):
    """WBS 3.5.2–3.5.5 — corte, ventas por periodo, más vendidos, insumos, mermas y PDF (reglas 5 y 11)."""

    def setUp(self):
        users = get_user_model().objects
        self.admin = users.create_user(username="dueno", password="x-9Lq!pr2", role="admin")
        self.cashier = users.create_user(username="caja", password="x-9Lq!pr3", role="cashier")
        category = Category.objects.create(name="Burritos")
        self.burrito = Dish.objects.create(name="Burrito de asada", category=category, price=Decimal("85.00"))
        self.coffee = Dish.objects.create(name="Café de olla", category=category, price=Decimal("30.00"))
        self.beef = Ingredient.objects.create(name="Asada", unit=Units.KG, stock=Decimal("10"),
                                              unit_cost=Decimal("200.00"))
        self.ground = Ingredient.objects.create(name="Café molido", unit=Units.KG, stock=Decimal("2"),
                                                unit_cost=Decimal("100.00"))
        Recipe.objects.create(dish=self.burrito, ingredient=self.beef, quantity=Decimal("0.150"))
        Recipe.objects.create(dish=self.coffee, ingredient=self.ground, quantity=Decimal("0.020"))
        self.session = cash.open_session(self.admin, Decimal("500.00"), device_timestamp=at(DAY, 7))

    def sell(self, burritos=0, coffees=0, method="efectivo", when=None):
        lines = []
        if burritos:
            lines.append({"platillo_id": self.burrito.pk, "precio_base_centavos": 8500, "cantidad": burritos})
        if coffees:
            lines.append({"platillo_id": self.coffee.pk, "precio_base_centavos": 3000, "cantidad": coffees})
        total = 8500 * burritos + 3000 * coffees
        return sales.confirm_sale(self.cashier, {"lineas": lines}, method, total, uuid=uuid4(),
                                  session_uuid=self.session.uuid, device_timestamp=when or at(DAY, 9))

    def test_period_ranges(self):
        self.assertEqual(reports.period_range("hoy", DAY), (DAY, DAY))
        self.assertEqual(reports.period_range("semana", DAY), (date(2026, 11, 2), date(2026, 11, 8)))
        self.assertEqual(reports.period_range("mes", DAY), (date(2026, 11, 1), date(2026, 11, 30)))
        self.assertEqual(reports.previous_range(date(2026, 11, 2), date(2026, 11, 8)),
                         (date(2026, 10, 26), date(2026, 11, 1)))

    def test_sales_by_period_nets_cancellations_and_payment_corrections(self):
        self.sell(burritos=2, when=at(DAY, 8, 30))                       # 170 cash
        moved = self.sell(coffees=1, when=at(DAY, 9))                    # 30 → transfer
        cancelled = self.sell(burritos=1, method="transferencia", when=at(DAY, 9, 30))
        sales.adjust_sale(self.admin, moved, "correccion_pago", new_payment_method="transferencia")
        sales.cancel_sale(self.admin, cancelled, "error_captura")
        result = reports.sales_by_period(DAY, DAY)
        self.assertEqual((result["total"], result["cash"], result["transfer"]),
                         (Decimal("200.00"), Decimal("170.00"), Decimal("30.00")))
        self.assertEqual((result["tickets"], result["cancelled"], result["average"]), (2, 1, Decimal("100.00")))
        self.assertEqual(result["chart"], [("08", Decimal("170.00")), ("09", Decimal("30.00"))])

    def test_a_sale_counts_on_its_device_day_and_the_week_chart_has_every_day(self):
        self.sell(burritos=1, when=at(DAY, 23, 50))
        week = reports.sales_by_period(*reports.period_range("semana", DAY))
        self.assertEqual([label for label, _ in week["chart"]], ["L", "M", "M", "J", "V", "S", "D"])
        self.assertEqual(week["chart"][2], ("M", Decimal("85.00")))
        self.assertEqual(reports.sales_by_period(date(2026, 11, 5), date(2026, 11, 5))["total"], Decimal("0.00"))
        month = reports.sales_by_period(*reports.period_range("mes", DAY))
        self.assertEqual([label for label, _ in month["chart"]], ["S1", "S2", "S3", "S4", "S5"])

    def test_top_dishes_skip_cancelled_sales_and_reverted_units(self):
        sale = self.sell(burritos=3, coffees=1)
        self.sell(coffees=1)
        self.sell(coffees=5)
        sales.adjust_sale(self.admin, sale, "error_captura", order_item=sale.order.items.get(dish=self.burrito),
                          quantity=1)
        sales.cancel_sale(self.admin, sales.Sale.objects.order_by("pk").last(), "error_captura")
        self.assertEqual(reports.top_dishes(DAY, DAY), [
            {"dish_id": self.burrito.pk, "name": "Burrito de asada", "units": 2},
            {"dish_id": self.coffee.pk, "name": "Café de olla", "units": 2},
        ])

    def test_ingredients_used_waste_and_profit(self):
        sale = self.sell(burritos=2, coffees=1)  # 0.300 kg beef ($60) and 0.020 kg coffee ($2)
        sales.adjust_sale(self.admin, sale, "error_captura", order_item=sale.order.items.get(dish=self.coffee),
                          quantity=1)
        register_waste(self.beef, Decimal("0.5"), self.admin, "Caducidad")
        today = timezone.localdate()
        used = reports.ingredients_used(DAY, today)
        self.assertEqual(used["items"], [{"name": "Asada", "unit": "kg",
                                          "quantity": Decimal("0.300"), "cost": Decimal("60.00")}])
        waste = reports.waste_by_period(DAY, today)
        self.assertEqual((waste["cost"], waste["count"], waste["items"][0]["reason"]),
                         (Decimal("100.00"), 1, "Caducidad"))
        result = reports.profit(DAY, today)
        self.assertEqual((result["sales"], result["cost"], result["amount"], result["margin"]),
                         (Decimal("170.00"), Decimal("60.00"), Decimal("110.00"), 65))

    def test_cash_close_while_open_and_after_closing(self):
        self.sell(burritos=2)
        self.sell(coffees=1, method="transferencia")
        result = reports.cash_close(self.session)
        self.assertEqual((result["cash"], result["transfer"], result["total"], result["expected_amount"]),
                         (Decimal("170.00"), Decimal("30.00"), Decimal("200.00"), Decimal("670.00")))
        self.assertEqual((result["tickets"], result["is_open"], result["cash_difference"]), (2, True, None))
        cash.close_session(self.admin, Decimal("660.00"))
        self.session.refresh_from_db()
        result = reports.cash_close(self.session)
        self.assertEqual((result["is_open"], result["closing_amount"], result["cash_difference"]),
                         (False, Decimal("660.00"), Decimal("-10.00")))

    def test_daily_sales_pdf(self):
        sale = self.sell(burritos=1, coffees=2, when=at(DAY, 10, 5))
        sales.cancel_sale(self.admin, self.sell(coffees=1, when=at(DAY, 11)), "devolucion")
        rows = reports.daily_sales(DAY)
        self.assertEqual(rows[0]["time"], "10:05")
        self.assertEqual(rows[0]["ticket"], str(sale.uuid)[:8])
        self.assertEqual((rows[0]["items"], rows[0]["total"], rows[1]["status"]),
                         ("1× Burrito de asada, 2× Café de olla", Decimal("145.00"), "Cancelada"))
        pdf = reports.export_daily_sales_pdf(DAY)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertTrue(reports.export_daily_sales_pdf(date(2026, 1, 1)).startswith(b"%PDF"))
