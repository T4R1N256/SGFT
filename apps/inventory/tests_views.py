"""
View and view–template contract tests for Inventario (WBS 3.2.5, 3.2.7, 3.2.8; interface 2.2.3). Owner: Yahir (DEC-31).

The device is activated with the cashier account and the padlock is opened as an Administrator, as accounts:admin_pin
does. HTMX requests carry the HX-Request header.
"""
import re
from collections import Counter
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Ingredient, Units
from apps.core.mixins import UNLOCKED_BY_KEY, UNLOCKED_UNTIL_KEY
from apps.inventory.models import MovementKind, StockMovement

HTMX = {"HTTP_HX_REQUEST": "true"}
LIST, PURCHASE, WASTE = "/inventory/", "/inventory/purchases/new/", "/inventory/waste/new/"


class ViewTestCase(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.admin = users.create_user(username="dueno", password="x-9Lq!pr2", role="admin")
        self.cashier = users.create_user(username="caja", password="x-9Lq!pr3", role="cashier")
        self.client.force_login(self.cashier)
        self.unlock()
        for name, unit, stock, min_stock in [("Tortilla de harina", Units.PIECE, "36", "40"),
                                             ("Carne asada", Units.KG, "8.5", "3"),
                                             ("Pollo deshebrado", Units.KG, "1.2", "3"),
                                             ("Huevo", Units.PIECE, "28", "30")]:
            Ingredient.objects.create(name=name, unit=unit, stock=Decimal(stock), min_stock=Decimal(min_stock),
                                      unit_cost=Decimal("10.00"))
        self.chicken = Ingredient.objects.get(name="Pollo deshebrado")

    def unlock(self):
        session = self.client.session
        session[UNLOCKED_UNTIL_KEY] = (timezone.now() + timedelta(minutes=30)).timestamp()
        session[UNLOCKED_BY_KEY] = self.admin.pk
        session.save()

    def assertUniqueIds(self, response):
        ids = Counter(re.findall(r'\sid="([^"]+)"', response.content.decode()))
        repeated = [i for i, n in ids.items() if n > 1]
        self.assertEqual(repeated, [], f"ids repetidos: {repeated}")

    def assertStartsWithId(self, response, tag, dom_id):
        self.assertTrue(response.content.decode().lstrip().startswith(f'<{tag} id="{dom_id}"'),
                        "el id destino va en la raíz del fragmento")


class AccessTests(ViewTestCase):
    def test_locked_asks_for_the_pin(self):
        self.client.session.flush()
        self.client.force_login(self.cashier)
        response = self.client.get(LIST)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "pin_required.html")
        response = self.client.post(PURCHASE, {}, **HTMX)
        self.assertEqual((response.status_code, response["HX-Retarget"]), (403, "#dialog"))
        self.assertFalse(StockMovement.objects.exists())

    def test_without_an_activated_device_goes_to_activation(self):
        self.client.logout()
        self.assertEqual(self.client.get(LIST).status_code, 302)


class IngredientListTests(ViewTestCase):
    """inventory:ingredient_list with the ingredients of the database."""

    def test_full_page_uses_base_and_components(self):
        response = self.client.get(LIST)
        for template in ("inventory/ingredient_list.html", "base.html", "components/page_header.html",
                         "components/ingredient_card.html", "components/stock_alert.html"):
            self.assertTemplateUsed(response, template)
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertUniqueIds(response)
        self.assertEqual(html.count("<article"), 4, "una tarjeta por insumo")
        self.assertIn("Existencias de insumos · 4 insumos", html)
        self.assertNotIn("Ordenar", html)
        self.assertNotIn("Filtros", html)

    def test_low_stock_lists_critical_first_then_low(self):
        html = self.client.get(LIST).content.decode().split('id="low-stock"')[1]
        names = re.findall(r'truncate sgft-texto-cuerpo-pequeno-medio text-texto-primario">([^<]+)<', html)
        self.assertEqual(names, ["Pollo deshebrado", "Huevo", "Tortilla de harina"])
        self.assertIn("Quedan 1.2 kg de 3 kg mínimos", html)

    def test_level_follows_rule_3(self):
        cards = {c["name"]: c for c in self.client.get(LIST).context["ingredients"]}
        self.assertEqual(cards["Huevo"]["level"], "bajo", "28 de 30: existencia <= mínimo")
        self.assertEqual(cards["Pollo deshebrado"]["level"], "critico", "1.2 <= la mitad de 3")
        self.assertEqual(cards["Carne asada"]["level"], "normal")
        self.assertEqual((cards["Carne asada"]["stock"], cards["Huevo"]["stock"]), (Decimal("8.5"), Decimal("28")))

    def test_search_returns_grid_fragment(self):
        response = self.client.get(LIST, {"q": "pollo"}, **HTMX)
        self.assertStartsWithId(response, "div", "ingredient-grid")
        self.assertEqual(response.content.decode().count("<article"), 1)

    def test_search_without_matches_and_empty_catalog(self):
        self.assertIn("Sin insumos que coincidan", self.client.get(LIST, {"q": "zzz"}, **HTMX).content.decode())
        Ingredient.objects.all().delete()
        self.assertIn("Agrega insumos para verlos", self.client.get(LIST, **HTMX).content.decode())

    def test_grid_refreshes_when_an_ingredient_is_created(self):
        html = self.client.get(LIST, **HTMX).content.decode()
        self.assertIn('hx-trigger="ingredient-created from:body"', html)


class StockFormTests(ViewTestCase):
    """inventory:register_purchase and inventory:register_waste with the inventory services."""

    def test_purchase_dialog_has_the_agreed_fields_and_the_ingredients(self):
        html = self.client.get(PURCHASE, **HTMX).content.decode()
        for name in ("ingredient", "quantity", "total_cost", "note"):
            self.assertIn(f'name="{name}"', html)
        self.assertIn(f'value="{self.chicken.pk}"', html)

    def test_invalid_purchase_is_422_in_the_dialog(self):
        response = self.client.post(PURCHASE, {"ingredient": "999", "quantity": "x", "total_cost": "0"}, **HTMX)
        self.assertEqual((response.status_code, response["HX-Retarget"]), (422, "#dialog"))
        html = response.content.decode()
        for message in ("Elige el insumo.", "Escribe la cantidad con números.",
                        "El costo total debe ser mayor que cero."):
            self.assertIn(message, html)
        self.assertFalse(StockMovement.objects.exists())

    def test_too_precise_quantity_comes_back_from_the_service(self):
        response = self.client.post(PURCHASE, {"ingredient": self.chicken.pk, "quantity": "1.2345",
                                               "total_cost": "100"}, **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertIn("a lo más 3 decimales", response.content.decode())

    def test_valid_purchase_adds_stock_in_the_admins_name_and_refreshes(self):
        response = self.client.post(PURCHASE, {"ingredient": self.chicken.pk, "quantity": "3",
                                               "total_cost": "$390.00", "note": "Mercado"}, **HTMX)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Compra de Pollo deshebrado registrada.", html)
        for dom_id in ("dialog", "ingredient-grid", "low-stock"):
            self.assertRegex(html, rf'id="{dom_id}"[^>]*hx-swap-oob="true"')
        self.chicken.refresh_from_db()
        self.assertEqual((self.chicken.stock, self.chicken.unit_cost), (Decimal("4.200"), Decimal("130.00")))
        movement = StockMovement.objects.get()
        self.assertEqual((movement.kind, movement.created_by, movement.note), (MovementKind.PURCHASE, self.admin,
                                                                              "Mercado"))

    def test_waste_other_reason_is_required_and_limited(self):
        base = {"ingredient": self.chicken.pk, "quantity": "0.5", "reason": "Otro"}
        response = self.client.post(WASTE, base, **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertIn("Especifica el motivo.", response.content.decode())
        response = self.client.post(WASTE, {**base, "other_reason": "x" * 51}, **HTMX)
        self.assertIn("Máximo 50 caracteres.", response.content.decode())
        response = self.client.post(WASTE, {**base, "other_reason": "Se cayó"}, **HTMX)
        self.assertEqual(response.status_code, 200)
        movement = StockMovement.objects.get()
        self.assertEqual((movement.kind, movement.quantity, movement.note, movement.created_by),
                         (MovementKind.WASTE, Decimal("-0.5"), "Se cayó", self.admin))

    def test_waste_keeps_the_chosen_reason_as_note(self):
        self.client.post(WASTE, {"ingredient": self.chicken.pk, "quantity": "2", "reason": "Caducidad"}, **HTMX)
        self.chicken.refresh_from_db()
        self.assertEqual(self.chicken.stock, Decimal("-0.800"), "puede quedar negativa (regla 10)")
        self.assertEqual(StockMovement.objects.get().note, "Caducidad")

    def test_waste_dialog_lists_the_agreed_reasons(self):
        html = self.client.get(WASTE, **HTMX).content.decode()
        for reason in ("Caducidad", "Mal almacenamiento", "Daño en empaque", "Maduración", "Otro"):
            self.assertIn(f'<option value="{reason}"', html)
        self.assertIn('maxlength="50"', html)
