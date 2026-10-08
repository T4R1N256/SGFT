"""
View and view–template contract tests for Caja y Reportes (WBS 3.5.1–3.5.7; interface 2.2.4). Owner: Yahir (DEC-31).

The views are called directly with RequestFactory, so the tests do not depend on urls.py (pending, see
rutas-pendientes.md). HTMX requests are simulated with the HX-Request header and django-htmx's HtmxDetails.
"""
import re
from collections import Counter

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase
from django_htmx.middleware import HtmxDetails

from apps.reports import views


class ViewTestCase(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def call(self, view, method="get", htmx=False, data=None, **kwargs):
        headers = {"HTTP_HX_REQUEST": "true"} if htmx else {}
        request = getattr(self.factory, method)("/", data or {}, **headers)
        request.user = AnonymousUser()
        request.htmx = HtmxDetails(request)
        return view(request, **kwargs)

    def assertUniqueIds(self, response):
        ids = Counter(re.findall(r'\sid="([^"]+)"', response.content.decode()))
        repeated = [i for i, n in ids.items() if n > 1]
        self.assertEqual(repeated, [], f"ids repetidos: {repeated}")

    def assertStartsWithId(self, response, tag, dom_id):
        self.assertTrue(response.content.decode().lstrip().startswith(f'<{tag} id="{dom_id}"'),
                        "el id destino va en la raíz del fragmento")


class CashTests(ViewTestCase):
    """reports:cash (3.5.1, 3.5.7): Caja, adapted from Yahir's screen to base.html and the components."""

    def test_full_page_uses_base_and_components_without_search(self):
        with self.assertTemplateUsed("reports/cash.html"), self.assertTemplateUsed("base.html"), \
                self.assertTemplateUsed("components/page_header.html"), self.assertTemplateUsed("components/kpi.html"), \
                self.assertTemplateUsed("components/bar_chart.html"), self.assertTemplateUsed("components/sync_status.html"):
            response = self.call(views.cash)
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertUniqueIds(response)
        self.assertNotIn('name="q"', html, "Caja no lleva buscador")
        self.assertIn("Última sincronización", html)

    def test_cards_order_starts_with_total_of_the_day(self):
        html = self.call(views.cash).content.decode()
        labels = re.findall(r'<article class="sgft-card[^"]*"\s+aria-label(?:ledby)?="([^"]+)"', html.split('id="cash-kpis"')[1])
        self.assertEqual(labels, ["Total de hoy", "Ganancias totales", "Mermas totales", "close-title"])

    def test_amounts_are_formatted_by_the_server_values(self):
        html = self.call(views.cash).content.decode()
        for text in ("$4,850.00", "$2,910.00", "$186.50", "$3,620.00", "$3,120.00", "$1,730.00", "Fondo inicial $500.00"):
            self.assertIn(text, html)

    def test_period_chip_returns_chart_fragment_with_one_active_chip(self):
        response = self.call(views.cash, htmx=True, data={"periodo": "semana"})
        self.assertStartsWithId(response, "article", "sales-chart")
        html = response.content.decode()
        self.assertEqual(html.count('aria-pressed="true"'), 1)
        self.assertEqual(re.search(r'aria-pressed="true"[^>]*>\s*(\w+)', html).group(1), "Semana")
        self.assertEqual(html.count('class="sr-only">'), 7, "una barra por día de la semana")

    def test_unknown_period_falls_back_to_today(self):
        html = self.call(views.cash, htmx=True, data={"periodo": "anio"}).content.decode()
        self.assertEqual(html.count('class="sr-only">'), 10, "una barra por hora")

    def test_no_sales_shows_centered_message(self):
        html = self.call(views.cash, htmx=True, data={"estado": "vacio"}).content.decode()
        self.assertIn("Sin ventas para este periodo", html)

    def test_pending_operations_are_shown_in_the_close_card(self):
        self.assertIn("2 operaciones pendientes de sincronizar", self.call(views.cash, data={"pendientes": "2"}).content.decode())
        self.assertIn("0 operaciones pendientes de sincronizar", self.call(views.cash).content.decode())


class ReportsTests(ViewTestCase):
    """reports:reports (3.5.2–3.5.4): Reportes, adapted from Yahir's screen to base.html and the components."""

    def test_full_page_uses_base_and_components_without_search(self):
        with self.assertTemplateUsed("reports/reports.html"), self.assertTemplateUsed("base.html"), \
                self.assertTemplateUsed("components/page_header.html"), self.assertTemplateUsed("components/list_row.html"), \
                self.assertTemplateUsed("components/rank_row.html"), self.assertTemplateUsed("components/period_chips.html"):
            response = self.call(views.reports)
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertUniqueIds(response)
        self.assertNotIn('name="q"', html, "Reportes no lleva buscador")
        self.assertNotIn("Calendario", html, "el campo de fecha ya abre el selector")

    def test_cards_order_and_selector_before_them(self):
        html = self.call(views.reports).content.decode()
        labels = re.findall(r'<article class="sgft-card[^"]*" aria-label="([^"]+)"', html)
        self.assertEqual(labels, ["Ventas", "Mermas", "Productos vendidos", "Insumos usados"])
        self.assertLess(html.index('aria-label="Periodo del reporte"'), html.index('aria-label="Ventas"'))

    def test_totals_match_the_sample_week(self):
        html = self.call(views.reports).content.decode()
        for text in ("$31,550.00", "$20,450.00", "$11,100.00", "Promedio $124.21", "$742.00", "720 uds.", "$9,230.00"):
            self.assertIn(text, html)

    def test_period_returns_columns_and_replaces_subtitle_out_of_band(self):
        response = self.call(views.reports, htmx=True, data={"periodo": "mes", "fecha": "2026-08-03"})
        self.assertStartsWithId(response, "div", "report-columns")
        html = response.content.decode()
        self.assertRegex(html, r'<p id="report-period" hx-swap-oob="true"[^>]*>Septiembre de 2026 · Corte mensual')
        self.assertIn('value="2026-08-03"', html)
        self.assertEqual(re.search(r'aria-pressed="true"[^>]*>\s*(\w+)', html).group(1), "Mes")

    def test_invalid_date_falls_back_to_the_default(self):
        html = self.call(views.reports, htmx=True, data={"fecha": "31/09"}).content.decode()
        self.assertIn('value="2026-09-21"', html)

    def test_no_sales_shows_centered_message_and_keeps_the_selector(self):
        html = self.call(views.reports, data={"estado": "vacio"}).content.decode()
        self.assertIn("Sin ventas para este periodo", html)
        self.assertIn('aria-label="Periodo del reporte"', html)


class ExportDailySalesPdfTests(ViewTestCase):
    """reports:export_daily_sales_pdf (3.5.5): the dialog downloads with a plain GET, not HTMX."""

    def test_dialog_submits_with_plain_get(self):
        html = self.call(views.export_daily_sales_pdf, htmx=True).content.decode()
        self.assertIn('method="get"', html)
        self.assertNotIn("hx-post", html)
        self.assertIn('name="day"', html)
        self.assertIn('value="2026-09-27"', html)

    def test_plain_get_downloads(self):
        response = self.call(views.export_daily_sales_pdf, data={"day": "2026-09-27"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("2026-09-27", response.content.decode())
