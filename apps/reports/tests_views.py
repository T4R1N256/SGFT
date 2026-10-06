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
