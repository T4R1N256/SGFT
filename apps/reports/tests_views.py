"""
View and view–template contract tests for Caja y Reportes (WBS 3.5.1–3.5.7; interface 2.2.4). Owner: Yahir (DEC-31).

The device is activated with the cashier account and the padlock is opened as an Administrator, as accounts:admin_pin
does. The sales go through pos.services.confirm_sale, as in the real screens. HTMX requests carry HX-Request.
"""
import re
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Category, Dish, Ingredient, Recipe, Units
from apps.core.mixins import UNLOCKED_BY_KEY, UNLOCKED_UNTIL_KEY
from apps.inventory.services import register_waste
from apps.pos import services as sales
from apps.pos import services_cash_session as cash

HTMX = {"HTTP_HX_REQUEST": "true"}
CASH, REPORTS, PDF = "/reports/cash/", "/reports/", "/reports/daily-sales.pdf"


class ViewTestCase(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.admin = users.create_user(username="dueno", password="x-9Lq!pr2", role="admin")
        self.cashier = users.create_user(username="caja", password="x-9Lq!pr3", role="cashier")
        self.client.force_login(self.cashier)
        session = self.client.session
        session[UNLOCKED_UNTIL_KEY] = (timezone.now() + timedelta(minutes=30)).timestamp()
        session[UNLOCKED_BY_KEY] = self.admin.pk
        session.save()
        category = Category.objects.create(name="Burritos")
        self.burrito = Dish.objects.create(name="Burrito de asada", category=category, price=Decimal("85.00"))
        self.coffee = Dish.objects.create(name="Café de olla", category=category, price=Decimal("30.00"))
        self.beef = Ingredient.objects.create(name="Carne asada", unit=Units.KG, stock=Decimal("10"),
                                              unit_cost=Decimal("200.00"))
        Recipe.objects.create(dish=self.burrito, ingredient=self.beef, quantity=Decimal("0.150"))
        Recipe.objects.create(dish=self.coffee, ingredient=self.beef, quantity=Decimal("0.001"))

    def open(self):
        self.session = cash.open_session(self.admin, Decimal("500.00"))
        return self.session

    def sell(self, burritos=0, coffees=0, method="efectivo", when=None):
        lines = []
        if burritos:
            lines.append({"platillo_id": self.burrito.pk, "precio_base_centavos": 8500, "cantidad": burritos})
        if coffees:
            lines.append({"platillo_id": self.coffee.pk, "precio_base_centavos": 3000, "cantidad": coffees})
        return sales.confirm_sale(self.cashier, {"lineas": lines}, method, 8500 * burritos + 3000 * coffees,
                                  uuid=uuid4(), session_uuid=self.session.uuid, device_timestamp=when or timezone.now())

    def assertUniqueIds(self, response):
        ids = Counter(re.findall(r'\sid="([^"]+)"', response.content.decode()))
        repeated = [i for i, n in ids.items() if n > 1]
        self.assertEqual(repeated, [], f"ids repetidos: {repeated}")

    def assertStartsWithId(self, response, tag, dom_id):
        self.assertTrue(response.content.decode().lstrip().startswith(f'<{tag} id="{dom_id}"'),
                        "el id destino va en la raíz del fragmento")


class AccessTests(ViewTestCase):
    def test_every_screen_asks_for_the_pin(self):
        self.client.session.flush()
        self.client.force_login(self.cashier)
        for url in (CASH, REPORTS, PDF):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)
                self.assertTemplateUsed(response, "pin_required.html")


class CashTests(ViewTestCase):
    """reports:cash (3.5.1, 3.5.7) with the open session and today's sales."""

    def setUp(self):
        super().setUp()
        self.open()
        self.sell(burritos=2)                           # $170 cash, 0.300 kg of beef ($60)
        self.sell(coffees=1, method="transferencia")    # $30 transfer, 0.001 kg ($0.20)
        register_waste(self.beef, Decimal("0.5"), self.admin, "Caducidad")  # $100

    def test_full_page_uses_base_and_components_without_search(self):
        response = self.client.get(CASH)
        for template in ("reports/cash.html", "base.html", "components/page_header.html", "components/kpi.html",
                         "components/bar_chart.html", "components/sync_status.html"):
            self.assertTemplateUsed(response, template)
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertUniqueIds(response)
        self.assertNotIn('name="q"', html, "Caja no lleva buscador")
        self.assertIn("Fondo inicial $500.00", html)

    def test_cards_order_starts_with_total_of_the_day(self):
        html = self.client.get(CASH).content.decode()
        labels = re.findall(r'<article class="sgft-card[^"]*"\s+aria-label(?:ledby)?="([^"]+)"',
                            html.split('id="cash-kpis"')[1])
        self.assertEqual(labels, ["Total de hoy", "Ganancias totales", "Mermas totales", "close-title"])

    def test_amounts_come_from_what_was_recorded(self):
        html = self.client.get(CASH).content.decode()
        for text in ("$200.00", "$170.00", "$30.00", "$139.80", "$100.00", "$670.00", "Margen del 70%",
                     "1 registro hoy", "Mayor merma: carne asada ($100.00, caducidad)", "50.0% de ventas"):
            self.assertIn(text, html)
        self.assertIn("Cerrar caja", html)

    def test_without_an_open_session_there_is_no_close_button(self):
        cash.close_session(self.admin, Decimal("670.00"))
        html = self.client.get(CASH).content.decode()
        self.assertIn("No hay un turno de caja abierto", html)
        self.assertNotIn("Cerrar caja", html)

    def test_period_chip_returns_chart_fragment_with_one_active_chip(self):
        response = self.client.get(CASH, {"periodo": "semana"}, **HTMX)
        self.assertStartsWithId(response, "article", "sales-chart")
        html = response.content.decode()
        self.assertEqual(html.count('aria-pressed="true"'), 1)
        self.assertEqual(re.search(r'aria-pressed="true"[^>]*>\s*(\w+)', html).group(1), "Semana")
        self.assertEqual(html.count('class="sr-only">'), 7, "una barra por día de la semana")

    def test_unknown_period_falls_back_to_today_with_one_bar_per_hour_sold(self):
        html = self.client.get(CASH, {"periodo": "anio"}, **HTMX).content.decode()
        self.assertIn(html.count('class="sr-only">'), (1, 2), "una barra por hora con ventas")

    def test_pending_operations_are_shown_in_the_close_card(self):
        self.assertIn("2 operaciones pendientes de sincronizar",
                      self.client.get(CASH, {"pendientes": "2"}).content.decode())
        self.assertIn("0 operaciones pendientes de sincronizar", self.client.get(CASH).content.decode())

    def test_top_bar_shows_the_session_total(self):
        response = self.client.get(CASH)
        self.assertEqual((response.context["cash_session_open"], response.context["session_total"]),
                         (True, Decimal("200.00")))


class CashEmptyTests(ViewTestCase):
    def test_no_sales_shows_centered_message(self):
        html = self.client.get(CASH, **HTMX).content.decode()
        self.assertIn("Sin ventas para este periodo", html)


class ReportsTests(ViewTestCase):
    """reports:reports (3.5.2–3.5.4) for the week of today (waste and stock movements carry today's date)."""

    def setUp(self):
        super().setUp()
        self.open()
        today = timezone.localdate()
        self.DAY = f"{today:%Y-%m-%d}"
        morning = timezone.make_aware(datetime(today.year, today.month, today.day, 9))
        self.sell(burritos=3, when=morning)
        self.sell(burritos=1, coffees=2, method="transferencia", when=morning + timedelta(hours=2))
        cancelled = self.sell(coffees=1, when=morning)
        sales.cancel_sale(self.admin, cancelled, "devolucion")

    def get(self, **data):
        return self.client.get(REPORTS, {"fecha": self.DAY, **data})

    def test_full_page_uses_base_and_components_without_search(self):
        response = self.get()
        for template in ("reports/reports.html", "base.html", "components/page_header.html",
                         "components/list_row.html", "components/rank_row.html", "components/period_chips.html"):
            self.assertTemplateUsed(response, template)
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertUniqueIds(response)
        self.assertNotIn('name="q"', html, "Reportes no lleva buscador")
        self.assertNotIn("Calendario", html, "el campo de fecha ya abre el selector")

    def test_cards_order_and_selector_before_them(self):
        html = self.get().content.decode()
        labels = re.findall(r'<article class="sgft-card[^"]*" aria-label="([^"]+)"', html)
        self.assertEqual(labels, ["Ventas", "Mermas", "Productos vendidos", "Insumos usados"])
        self.assertLess(html.index('aria-label="Periodo del reporte"'), html.index('aria-label="Ventas"'))

    def test_totals_of_the_week(self):
        html = self.get().content.decode()
        for text in ("$400.00", "$255.00", "$145.00", "Tickets: 2", "Promedio $200.00", "4 uds.", "2 uds.",
                     "6 uds.", "Devolución", "0.602 kg"):
            self.assertIn(text, html)

    def test_period_returns_columns_and_replaces_subtitle_out_of_band(self):
        response = self.client.get(REPORTS, {"periodo": "mes", "fecha": "2026-11-03"}, **HTMX)
        self.assertStartsWithId(response, "div", "report-columns")
        html = response.content.decode()
        self.assertRegex(html, r'<p id="report-period" hx-swap-oob="true"[^>]*>Noviembre de 2026 · Corte mensual')
        self.assertIn('value="2026-11-03"', html)
        self.assertEqual(re.search(r'aria-pressed="true"[^>]*>\s*(\w+)', html).group(1), "Mes")

    def test_week_and_day_labels(self):
        html = self.client.get(REPORTS, {"fecha": "2026-11-04"}, **HTMX).content.decode()
        self.assertIn("Semana del 2 al 8 de noviembre de 2026 · Corte semanal", html)
        html = self.client.get(REPORTS, {"fecha": "2026-10-29"}, **HTMX).content.decode()
        self.assertIn("Semana del 26 de octubre al 1 de noviembre de 2026", html)
        html = self.client.get(REPORTS, {"periodo": "hoy", "fecha": "2026-11-04"}, **HTMX).content.decode()
        self.assertIn("Miércoles 4 de noviembre de 2026 · Corte del día", html)

    def test_invalid_date_falls_back_to_today(self):
        html = self.client.get(REPORTS, {"fecha": "31/09"}, **HTMX).content.decode()
        self.assertIn(f'value="{timezone.localdate():%Y-%m-%d}"', html)

    def test_no_sales_shows_centered_message_and_keeps_the_selector(self):
        html = self.client.get(REPORTS, {"fecha": "2026-01-15"}).content.decode()
        self.assertIn("Sin ventas para este periodo", html)
        self.assertIn('aria-label="Periodo del reporte"', html)


class ExportDailySalesPdfTests(ViewTestCase):
    """reports:export_daily_sales_pdf (3.5.5): the dialog downloads with a plain GET, not HTMX."""

    def test_dialog_submits_with_plain_get(self):
        html = self.client.get(PDF, **HTMX).content.decode()
        self.assertIn('method="get"', html)
        self.assertNotIn("hx-post", html)
        self.assertIn('name="day"', html)
        self.assertIn(f'value="{timezone.localdate():%Y-%m-%d}"', html)

    def test_plain_get_downloads_the_pdf(self):
        self.open()
        self.sell(burritos=1)
        response = self.client.get(PDF, {"day": f"{timezone.localdate():%Y-%m-%d}"})
        self.assertEqual((response.status_code, response["Content-Type"]), (200, "application/pdf"))
        self.assertIn(f'filename="ventas-{timezone.localdate():%Y-%m-%d}.pdf"', response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))
