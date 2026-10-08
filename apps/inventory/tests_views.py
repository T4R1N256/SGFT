"""
View and view–template contract tests for Inventario (WBS 3.2.5, 3.2.7, 3.2.8; interface 2.2.3). Owner: Yahir (DEC-31).

The views are called directly with RequestFactory, so the tests do not depend on urls.py (pending, see
rutas-pendientes.md). HTMX requests are simulated with the HX-Request header and django-htmx's HtmxDetails.
"""
import re
from collections import Counter

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase
from django_htmx.middleware import HtmxDetails

from apps.inventory import views


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


class IngredientListTests(ViewTestCase):
    """inventory:ingredient_list: Inventario, adapted from Yahir's screen to base.html and the components."""

    def test_full_page_uses_base_and_components(self):
        with self.assertTemplateUsed("inventory/ingredient_list.html"), self.assertTemplateUsed("base.html"), \
                self.assertTemplateUsed("components/page_header.html"), self.assertTemplateUsed("components/ingredient_card.html"), \
                self.assertTemplateUsed("components/stock_alert.html"), self.assertTemplateUsed("components/callout.html"):
            response = self.call(views.ingredient_list)
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertUniqueIds(response)
        self.assertEqual(html.count("<article"), 8, "una tarjeta por insumo")
        self.assertIn("Última sincronización", html)
        self.assertNotIn("Ordenar", html)
        self.assertNotIn("Filtros", html)

    def test_low_stock_lists_critical_first_then_low(self):
        html = self.call(views.ingredient_list).content.decode().split('id="low-stock"')[1]
        names = re.findall(r'truncate sgft-texto-cuerpo-pequeno-medio text-texto-primario">([^<]+)<', html)
        self.assertEqual(names, ["Pollo deshebrado", "Tortilla de harina", "Huevo"])
        self.assertIn("Crítico", html)

    def test_level_follows_rule_3(self):
        levels = {i["name"]: i["level"] for i in views._ingredients()}
        self.assertEqual(levels["Huevo"], "bajo", "28 de 30: existencia <= mínimo")
        self.assertEqual(levels["Pollo deshebrado"], "critico")
        self.assertEqual(levels["Carne asada"], "normal")

    def test_search_returns_grid_fragment(self):
        response = self.call(views.ingredient_list, htmx=True, data={"q": "pollo"})
        self.assertStartsWithId(response, "div", "ingredient-grid")
        self.assertEqual(response.content.decode().count("<article"), 1)

    def test_search_without_matches_shows_message(self):
        html = self.call(views.ingredient_list, htmx=True, data={"q": "zzz"}).content.decode()
        self.assertIn("Sin insumos que coincidan", html)

    def test_grid_refreshes_when_an_ingredient_is_created(self):
        html = self.call(views.ingredient_list, htmx=True).content.decode()
        self.assertIn('hx-trigger="ingredient-created from:body"', html)


class StockFormTests(ViewTestCase):
    """inventory:register_purchase and inventory:register_waste."""

    def test_purchase_dialog_has_the_agreed_fields(self):
        html = self.call(views.register_purchase, htmx=True).content.decode()
        for name in ("ingredient", "quantity", "total_cost", "note"):
            self.assertIn(f'name="{name}"', html)

    def test_invalid_purchase_is_422_in_the_dialog(self):
        response = self.call(views.register_purchase, method="post", htmx=True,
                             data={"ingredient": "3", "quantity": "x", "total_cost": "0"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response["HX-Retarget"], "#dialog")
        html = response.content.decode()
        self.assertIn("Escribe la cantidad con números.", html)
        self.assertIn("El costo total debe ser mayor que cero.", html)

    def test_valid_purchase_shows_message_and_refreshes_out_of_band(self):
        response = self.call(views.register_purchase, method="post", htmx=True,
                             data={"ingredient": "3", "quantity": "3", "total_cost": "390"})
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Compra de Pollo deshebrado registrada.", html)
        for dom_id in ("dialog", "ingredient-grid", "low-stock"):
            self.assertRegex(html, rf'id="{dom_id}"[^>]*hx-swap-oob="true"')

    def test_waste_other_reason_is_required_and_limited(self):
        base = {"ingredient": "1", "quantity": "2", "reason": "Otro"}
        response = self.call(views.register_waste, method="post", htmx=True, data=base)
        self.assertEqual(response.status_code, 422)
        self.assertIn("Especifica el motivo.", response.content.decode())
        response = self.call(views.register_waste, method="post", htmx=True, data={**base, "other_reason": "x" * 51})
        self.assertIn("Máximo 50 caracteres.", response.content.decode())
        response = self.call(views.register_waste, method="post", htmx=True, data={**base, "other_reason": "Se cayó"})
        self.assertEqual(response.status_code, 200)

    def test_waste_dialog_lists_the_agreed_reasons(self):
        html = self.call(views.register_waste, htmx=True).content.decode()
        for reason in ("Caducidad", "Mal almacenamiento", "Daño en empaque", "Maduración", "Otro"):
            self.assertIn(f'<option value="{reason}"', html)
        self.assertIn('maxlength="50"', html)
