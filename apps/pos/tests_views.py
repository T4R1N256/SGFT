"""
View and view–template contract tests for Nueva venta (WBS 3.3.1–3.3.3, 3.3.5, 3.5.1, 3.5.7). Owner: Tarín (DEC-31).

The device is activated with the cashier account; opening and closing the till open the padlock as an
Administrator, as accounts:admin_pin does. HTMX requests carry the HX-Request header.
"""
import re
from collections import Counter
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Category, Dish, Ingredient, Recipe, Units
from apps.core.mixins import UNLOCKED_BY_KEY, UNLOCKED_UNTIL_KEY
from apps.inventory.models import MovementKind, StockMovement
from apps.pos.models import CashRegisterSession, Modifier, ModifierKind, PaymentMethod, Sale, SessionStatus
from apps.pos.services_cash_session import open_session

HTMX = {"HTTP_HX_REQUEST": "true"}
BUILDER, DISHES, PAYMENT, CONFIRM = "/pos/", "/pos/dishes/", "/pos/order/payment-method/", "/pos/order/confirm/"
OPEN, CLOSE = "/pos/cash-session/open/", "/pos/cash-session/close/"


def add_url(dish):
    return f"/pos/dishes/{dish.pk}/add/"


class ViewTestCase(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.admin = users.create_user(username="dueno", password="x-9Lq!pr2", role="admin")
        self.cashier = users.create_user(username="caja", password="x-9Lq!pr3", role="cashier")
        self.client.force_login(self.cashier)
        self.burritos = Category.objects.create(name="Burritos", emoji="🌯")
        self.drinks = Category.objects.create(name="Bebidas", emoji="🥤")
        Category.objects.create(name="Guisados", emoji="🍲")  # no active dish: no chip
        self.tortilla = Ingredient.objects.create(name="Tortilla de harina", unit=Units.PIECE, stock=Decimal("50"),
                                                  min_stock=Decimal("10"))
        self.beef = Ingredient.objects.create(name="Carne asada", unit=Units.KG, stock=Decimal("5"),
                                              min_stock=Decimal("1"))
        self.cheese = Ingredient.objects.create(name="Queso chihuahua", unit=Units.KG, stock=Decimal("3"),
                                                min_stock=Decimal("0.5"))
        self.onion = Ingredient.objects.create(name="Cebolla", unit=Units.KG, stock=Decimal("2"),
                                               min_stock=Decimal("0.2"))
        self.coffee = Ingredient.objects.create(name="Café molido", unit=Units.KG, stock=Decimal("1"),
                                                min_stock=Decimal("0.2"))
        self.asada = Dish.objects.create(name="Burrito de asada", category=self.burritos, price=Decimal("75.00"))
        for ingredient, quantity in ((self.tortilla, "1"), (self.beef, "0.150"), (self.onion, "0.020")):
            Recipe.objects.create(dish=self.asada, ingredient=ingredient, quantity=Decimal(quantity))
        self.coffee_dish = Dish.objects.create(name="Café de olla", category=self.drinks, price=Decimal("25.00"))
        Recipe.objects.create(dish=self.coffee_dish, ingredient=self.coffee, quantity=Decimal("0.020"))
        Dish.objects.create(name="Tamal", category=self.burritos, price=Decimal("30.00"), is_active=False)
        self.extra_cheese = Modifier.objects.create(dish=self.asada, ingredient=self.cheese, kind=ModifierKind.ADD,
                                                    price_adjustment=Decimal("15.00"), quantity=Decimal("0.030"))
        self.no_onion = Modifier.objects.create(dish=self.asada, ingredient=self.onion, kind=ModifierKind.REMOVE)

    def unlock(self):
        session = self.client.session
        session[UNLOCKED_UNTIL_KEY] = (timezone.now() + timedelta(minutes=30)).timestamp()
        session[UNLOCKED_BY_KEY] = self.admin.pk
        session.save()

    def open_cash(self, amount="500.00"):
        return open_session(self.admin, Decimal(amount))

    def add(self, dish, times=1):
        for _ in range(times):
            response = self.client.post(add_url(dish), **HTMX)
        return response

    def line_id(self):
        return self.client.session["pos_order"]["lines"][0]["id"]

    def assertUniqueIds(self, response):
        ids = Counter(re.findall(r'\sid="([^"]+)"', response.content.decode()))
        repeated = [i for i, n in ids.items() if n > 1]
        self.assertEqual(repeated, [], f"ids repetidos: {repeated}")

    def assertStartsWithId(self, response, tag, dom_id):
        self.assertTrue(response.content.decode().lstrip().startswith(f'<{tag} id="{dom_id}"'),
                        "el id destino va en la raíz del fragmento")


class HomeTests(TestCase):
    """The site root opens Nueva venta (config/urls.py)."""

    def test_root_redirects_to_order_builder(self):
        response = self.client.get("/")
        self.assertRedirects(response, reverse("pos:order_builder"), fetch_redirect_response=False)


class AccessTests(ViewTestCase):
    def test_without_session_goes_to_activation(self):
        self.client.logout()
        self.assertEqual(self.client.get(BUILDER).status_code, 302)
        self.assertEqual(self.client.post(add_url(self.asada), **HTMX).status_code, 401)

    def test_opening_and_closing_ask_for_the_pin(self):
        for url in (OPEN, CLOSE):
            response = self.client.get(url, **HTMX)
            self.assertEqual((response.status_code, response["HX-Retarget"]), (403, "#dialog"))
            self.assertTemplateUsed(response, "components/pin_dialog.html")
        self.client.post(OPEN, {"opening_amount": "500"}, **HTMX)
        self.assertFalse(CashRegisterSession.objects.exists())


class OrderBuilderTests(ViewTestCase):
    def test_closed_cash_disables_content_and_offers_open(self):
        response = self.client.get(BUILDER)
        self.assertTemplateUsed(response, "pos/order_builder.html")
        html = response.content.decode()
        self.assertIn("La caja está cerrada", html)
        self.assertIn("inert", html)
        self.assertRegex(html, r'Caja<span class="sr-only"> cerrada</span>')
        self.assertNotIn('aria-labelledby="open-cash-title"', html)  # locked: the button asks for the PIN first
        self.assertUniqueIds(response)

    def test_closed_cash_with_the_padlock_open_shows_the_open_dialog(self):
        self.unlock()
        dialog = self.client.get(BUILDER).content.decode().split('<div id="dialog">')[1]
        self.assertIn('aria-labelledby="open-cash-title"', dialog)
        self.assertNotIn('name="pin"', dialog)  # online the padlock already identified the Administrator
        self.assertIn('name="opening_amount"', dialog)

    def test_open_cash_lists_the_active_dishes_from_the_catalog(self):
        self.open_cash()
        response = self.client.get(BUILDER)
        html = response.content.decode().split('<template x-if="sinRed">')[0]  # the server's area, not the offline one
        self.assertIn('id="sale-area"', html)
        self.assertIn("Burrito de asada", html)
        self.assertIn("$75.00", html)
        self.assertNotIn("Tamal", html)
        self.assertNotIn("La caja está cerrada", html)
        self.assertIn(f"Turno del {timezone.localdate():%d/%m/%Y}", html)
        self.assertIn("Toca un platillo para agregarlo", html)
        self.assertNotIn("Alerta stock", html)
        self.assertNotIn("Guisados", html)
        self.assertUniqueIds(response)

    def test_low_stock_shows_the_alert(self):
        self.open_cash()
        Ingredient.objects.filter(pk=self.beef.pk).update(stock=Decimal("0.5"))
        html = self.client.get(BUILDER).content.decode()
        self.assertIn("Alerta stock", html)
        self.assertIn("1 insumo bajo · Ver inventario", html)

    def test_htmx_returns_only_the_fragment(self):
        response = self.client.get(BUILDER, **HTMX)
        self.assertTemplateUsed(response, "pos/partials/sale_area.html")
        self.assertTemplateNotUsed(response, "base.html")
        self.assertStartsWithId(response, "div", "sale-area")


class DishListTests(ViewTestCase):
    def test_without_htmx_redirects(self):
        self.assertEqual(self.client.get(DISHES).status_code, 302)

    def test_filters_by_category_and_marks_active_chip_out_of_band(self):
        response = self.client.get(DISHES, {"category": self.drinks.pk}, **HTMX)
        html = response.content.decode()
        self.assertIn("Café de olla", html)
        self.assertNotIn("Burrito de asada", html)
        self.assertIn('id="category-chips" hx-swap-oob="true"', html)
        self.assertRegex(html, r'aria-pressed="true"[^>]*>\s*Bebidas')
        self.assertUniqueIds(response)

    def test_search_without_results_shows_centered_message(self):
        self.assertIn("Agrega platillos para verlos", self.client.get(DISHES, {"q": "pizza"}, **HTMX).content.decode())


class OrderSummaryTests(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.open_cash()

    def test_add_item_without_open_cash_is_409(self):
        CashRegisterSession.objects.update(status=SessionStatus.CLOSED)
        response = self.add(self.asada)
        self.assertEqual((response.status_code, response["HX-Retarget"]), (409, "#messages"))

    def test_add_item_sums_and_returns_ticket_and_card_out_of_band(self):
        response = self.add(self.asada, 2)
        self.assertTemplateUsed(response, "pos/partials/order_summary.html")
        self.assertStartsWithId(response, "aside", "order-summary")
        html = response.content.decode()
        self.assertIn(f'id="dish-{self.asada.pk}" hx-swap-oob="true"', html)
        self.assertIn("2 artículos", html)
        self.assertIn("$150.00", html)
        self.assertUniqueIds(response)

    def test_inactive_dish_cannot_be_added(self):
        hidden = Dish.objects.get(name="Tamal")
        self.assertEqual(self.add(hidden).status_code, 404)

    def test_remove_item_and_remove_dish(self):
        self.add(self.asada, 3)
        self.client.post(f"/pos/items/{self.line_id()}/remove/", **HTMX)
        response = self.client.post(f"/pos/dishes/{self.asada.pk}/remove/", **HTMX)
        self.assertIn("1 artículo", response.content.decode())
        response = self.client.post(f"/pos/dishes/{self.asada.pk}/remove/", **HTMX)
        self.assertIn("Toca un platillo para agregarlo", response.content.decode())

    def test_modifiers_dialog_and_price(self):
        self.add(self.asada, 2)
        url = f"/pos/items/{self.line_id()}/modifiers/"
        response = self.client.get(url, **HTMX)
        self.assertTemplateUsed(response, "pos/partials/line_modifiers.html")
        html = response.content.decode()
        self.assertIn("Extra queso chihuahua (+$15.00)", html)
        self.assertIn("Sin cebolla", html)
        response = self.client.post(url, {"modifier": [self.extra_cheese.pk, self.no_onion.pk]}, **HTMX)
        html = response.content.decode()
        self.assertIn("Extra queso chihuahua (+$15.00) · Sin cebolla", html)
        self.assertIn("$180.00", html)  # (75 + 15) × 2; «sin» does not change the price
        self.assertIn('id="dialog" hx-swap-oob="true"', html)

    def test_a_line_with_the_same_modifiers_merges(self):
        self.add(self.asada)
        self.client.post(f"/pos/items/{self.line_id()}/modifiers/", {"modifier": [self.no_onion.pk]}, **HTMX)
        self.add(self.asada)  # a plain one: a second line
        self.assertEqual(len(self.client.session["pos_order"]["lines"]), 2)
        plain = self.client.session["pos_order"]["lines"][1]["id"]
        self.client.post(f"/pos/items/{plain}/modifiers/", {"modifier": [self.no_onion.pk]}, **HTMX)
        lines = self.client.session["pos_order"]["lines"]
        self.assertEqual([(line["quantity"], line["modifiers"]) for line in lines], [(2, [self.no_onion.pk])])

    def test_dish_without_modifiers_has_no_customize_button(self):
        html = self.add(self.coffee_dish).content.decode()
        self.assertNotIn("Personalizar", html)

    def test_payment_method_selected_by_server(self):
        self.add(self.asada)
        response = self.client.post(PAYMENT, {"method": "transferencia"}, **HTMX)
        selected = r'(?s)sgft-btn--seleccionado.*?value="transferencia"|value="transferencia".*?sgft-btn--seleccionado'
        self.assertRegex(response.content.decode(), selected)

    def test_invalid_payment_method_is_retargeted_to_messages(self):
        response = self.client.post(PAYMENT, {"method": "tarjeta"}, **HTMX)
        self.assertEqual((response.status_code, response["HX-Retarget"]), (422, "#messages"))
        self.assertIn("efectivo o transferencia", response.content.decode())


class ConfirmSaleTests(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.session = self.open_cash()

    def test_confirm_records_the_sale_deducts_and_empties_the_ticket(self):
        self.add(self.asada, 2)
        self.client.post(f"/pos/items/{self.line_id()}/modifiers/", {"modifier": [self.extra_cheese.pk]}, **HTMX)
        self.add(self.coffee_dish)
        self.client.post(PAYMENT, {"method": "transferencia"}, **HTMX)
        response = self.client.post(CONFIRM, **HTMX)
        sale = Sale.objects.get()
        self.assertEqual((sale.charged_total, sale.payment_method, sale.cash_session, sale.created_by),
                         (Decimal("205.00"), PaymentMethod.TRANSFER, self.session, self.cashier))
        self.assertFalse(sale.needs_review)
        self.assertTrue(StockMovement.objects.filter(sale_uuid=sale.uuid, kind=MovementKind.SALE).exists())
        self.cheese.refresh_from_db()
        self.assertEqual(self.cheese.stock, Decimal("2.940"))
        html = response.content.decode()
        self.assertIn("Toca un platillo para agregarlo", html)
        self.assertIn('id="session-total" hx-swap-oob="true"', html)
        self.assertIn("$205.00", html)
        self.assertIn('id="dish-list" hx-swap-oob="true"', html)
        self.assertNotIn("sgft-dish-card__qty", html)
        self.assertNotIn("pos_order", self.client.session)
        self.assertUniqueIds(response)

    def test_empty_ticket_is_422(self):
        response = self.client.post(CONFIRM, **HTMX)
        self.assertEqual((response.status_code, response["HX-Retarget"]), (422, "#messages"))
        self.assertFalse(Sale.objects.exists())

    def test_dish_without_recipe_is_422_and_keeps_the_ticket(self):
        Recipe.objects.filter(dish=self.coffee_dish).delete()
        self.add(self.coffee_dish)
        response = self.client.post(CONFIRM, **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertIn("sin receta", response.content.decode())
        self.assertFalse(Sale.objects.exists())
        self.assertIn("pos_order", self.client.session)

    def test_closed_cash_is_409(self):
        self.add(self.asada)
        CashRegisterSession.objects.update(status=SessionStatus.CLOSED)
        self.assertEqual(self.client.post(CONFIRM, **HTMX).status_code, 409)
        self.assertFalse(Sale.objects.exists())


class OpenSessionTests(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.unlock()

    def test_get_returns_dialog_without_pin_boxes(self):
        response = self.client.get(OPEN, **HTMX)
        self.assertTemplateUsed(response, "pos/partials/open_cash_session.html")
        html = response.content.decode()
        self.assertNotIn('name="pin"', html)
        self.assertIn('name="opening_amount"', html)

    def test_invalid_amount_is_422_retargeted_to_dialog(self):
        response = self.client.post(OPEN, {"opening_amount": "abc"}, **HTMX)
        self.assertEqual((response.status_code, response["HX-Retarget"]), (422, "#dialog"))
        self.assertIn("Escribe el fondo inicial", response.content.decode())
        self.assertFalse(CashRegisterSession.objects.exists())

    def test_valid_open_records_the_admin_and_updates_the_screen(self):
        response = self.client.post(OPEN, {"opening_amount": "$1,500.00"}, **HTMX)
        self.assertEqual(response.status_code, 200)
        session = CashRegisterSession.objects.get()
        self.assertEqual((session.opened_by, session.opening_amount), (self.admin, Decimal("1500.00")))
        html = response.content.decode()
        self.assertIn('id="cash-status" hx-swap-oob="true"', html)
        self.assertRegex(html, r'Caja<span class="sr-only"> abierta</span>')
        self.assertIn('id="dialog" hx-swap-oob="true"', html)
        self.assertUniqueIds(response)

    def test_second_session_of_the_day_is_422(self):
        self.client.post(OPEN, {"opening_amount": "500"}, **HTMX)
        CashRegisterSession.objects.update(status=SessionStatus.CLOSED)
        response = self.client.post(OPEN, {"opening_amount": "500"}, **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertIn("solo hay uno por jornada", response.content.decode())


class CloseSessionTests(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.unlock()

    def test_without_open_session_is_409(self):
        response = self.client.get(CLOSE, **HTMX)
        self.assertEqual(response.status_code, 409)
        self.assertIn("No hay un turno de caja abierto", response.content.decode())

    def test_get_shows_the_expected_cash(self):
        self.open_cash("500.00")
        self.add(self.asada)
        self.client.post(CONFIRM, **HTMX)
        response = self.client.get(CLOSE, **HTMX)
        self.assertEqual(response.status_code, 200)
        self.assertIn("$575.00", response.content.decode())

    def test_pending_operations_are_409_in_the_dialog(self):
        self.open_cash()
        response = self.client.post(CLOSE, {"closing_amount": "500"}, HTTP_X_PENDIENTES="2", **HTMX)
        self.assertEqual((response.status_code, response["HX-Retarget"]), (409, "#dialog"))
        self.assertIn("faltan 2 ventas por sincronizar", response.content.decode())
        self.assertEqual(CashRegisterSession.objects.get().status, SessionStatus.OPEN)

    def test_invalid_amount_is_422_in_the_dialog(self):
        self.open_cash()
        response = self.client.post(CLOSE, {"closing_amount": "abc"}, **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertIn("Escribe el efectivo contado", response.content.decode())

    def test_valid_close_records_the_difference_and_redirects(self):
        self.open_cash("500.00")
        response = self.client.post(CLOSE, {"closing_amount": "480.00"}, **HTMX)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["HX-Redirect"], BUILDER)
        session = CashRegisterSession.objects.get()
        self.assertEqual((session.status, session.closed_by, session.cash_difference),
                         (SessionStatus.CLOSED, self.admin, Decimal("-20.00")))
        page = self.client.get(BUILDER).content.decode()
        self.assertIn("Caja cerrada, diferencia de −$20.00.", page)


class PwaTests(ViewTestCase):
    """WBS 3.4.1, 3.4.2: the installable app and its service worker."""

    def test_service_worker_is_served_from_pos_for_the_whole_site(self):
        self.client.logout()  # the browser fetches it by itself, with or without a session
        response = self.client.get("/pos/sw.js")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/javascript"))
        self.assertEqual(response["Service-Worker-Allowed"], "/")
        self.assertIn("no-cache", response["Cache-Control"])
        body = response.content.decode()
        self.assertIn("workbox-sw.js", body)
        self.assertIn('"/static/pos/pricing.js"', body)

    def test_every_precached_static_file_exists(self):
        from django.contrib.staticfiles import finders
        body = self.client.get("/pos/sw.js").content.decode()
        files = re.findall(r'"/static/([^"]+)"', body)
        self.assertGreater(len(files), 5)
        for path in files:
            self.assertIsNotNone(finders.find(path), path)

    def test_manifest_starts_in_nueva_venta(self):
        import json
        from django.contrib.staticfiles import finders
        with open(finders.find("pos/manifest.json"), encoding="utf-8") as source:
            manifest = json.load(source)
        self.assertEqual((manifest["start_url"], manifest["scope"], manifest["display"]), ("/pos/", "/", "standalone"))
        for icon in manifest["icons"]:
            self.assertIsNotNone(finders.find(icon["src"].removeprefix("/static/")), icon["src"])

    def test_nueva_venta_links_the_manifest_and_registers_the_worker(self):
        html = self.client.get(BUILDER).content.decode()
        self.assertIn('<link rel="manifest" href="/static/pos/manifest.json">', html)
        self.assertIn('src="/static/pos/pwa.js"', html)
        self.assertIn('rel="apple-touch-icon"', html)


class OfflineDataTests(ViewTestCase):
    """WBS 3.4.3, 3.4.4: what Nueva venta leaves on the device for working without network."""

    def data(self):
        import json
        html = self.client.get(BUILDER).content.decode()
        match = re.search(r'<script id="datos-sin-red" type="application/json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(match, "la página completa trae los datos sin red")
        return json.loads(match.group(1))

    def test_menu_in_cents_with_modifiers_and_spanish_keys(self):
        data = self.data()
        dishes = {p["nombre"]: p for p in data["catalogo"]["platillos"]}
        self.assertNotIn("Tamal", dishes)
        asada = dishes["Burrito de asada"]
        self.assertEqual((asada["precio_centavos"], asada["categoria_id"], asada["emoji"]),
                         (7500, self.burritos.pk, "🌯"))
        self.assertIn({"id": self.extra_cheese.pk, "tipo": "agregar", "insumo_id": self.cheese.pk,
                       "nombre": "Extra queso chihuahua (+$15.00)", "ajuste_centavos": 1500}, asada["modificadores"])
        self.assertIn({"id": self.no_onion.pk, "tipo": "quitar", "insumo_id": self.onion.pk,
                       "nombre": "Sin cebolla", "ajuste_centavos": 0}, asada["modificadores"])
        self.assertEqual([c["nombre"] for c in data["catalogo"]["categorias"]], ["Bebidas", "Burritos"])
        self.assertEqual(data["usuario"]["id"], self.cashier.pk)

    def test_session_and_verifiers_of_active_admins_only(self):
        self.assertIsNone(self.data()["turno"])
        session = self.open_cash()
        get_user_model().objects.create_user(username="exdueno", password="135790", role="admin", is_active=False)
        data = self.data()
        self.assertEqual(data["turno"], {"uuid": str(session.uuid), "fecha": session.business_date.isoformat()})
        self.assertEqual(data["verificadores"], [])  # the admin of setUp has no 6-digit PIN
        self.admin.set_password("482913")
        self.admin.save()
        [verifier] = self.data()["verificadores"]
        self.assertEqual(verifier["usuario_id"], self.admin.pk)
        self.assertEqual((verifier["sal"], verifier["verificador"]),
                         (self.admin.pin_verifier_salt, self.admin.pin_verifier))
        self.assertNotIn("482913", self.client.get(BUILDER).content.decode())

    def test_offline_client_is_loaded_and_htmx_fragments_skip_the_data(self):
        html = self.client.get(BUILDER).content.decode()
        for script in ("dexie@4.0.10", "/static/pos/pricing.js", "/static/pos/db.js", "/static/pos/offline.js"):
            self.assertIn(script, html)
        self.assertIn('x-data="ventaSinRed"', html)
        self.assertIn('href="#sincronizar"', html)
        self.assertIn("data-sgft-pendientes", html)
        self.assertNotIn("datos-sin-red", self.client.get(BUILDER, **HTMX).content.decode())

    def test_every_page_with_a_session_loads_the_offline_client(self):
        # Caja closes the till from another page: it must also sync and send X-Pendientes (rule 5).
        self.assertIn("/static/pos/offline.js", self.client.get("/catalog/").content.decode())
        self.assertNotIn("/static/pos/offline.js", self.client_class().get("/accounts/activate/").content.decode())

    def test_service_worker_precaches_the_offline_client(self):
        body = self.client.get("/pos/sw.js").content.decode()
        for path in ('"/static/pos/db.js"', '"/static/pos/offline.js"', "dexie@4.0.10"):
            self.assertIn(path, body)


class CashStateTests(ViewTestCase):
    """apps.pos.context_processors.cash_session: every screen shows the real cash state in the top bar."""

    def test_other_screens_show_the_open_session_and_its_total(self):
        self.unlock()
        for url in ("/catalog/", "/inventory/"):
            self.assertRegex(self.client.get(url).content.decode(), r'Caja<span class="sr-only"> cerrada</span>')
        self.open_cash()
        self.add(self.asada)
        self.client.post(CONFIRM, **HTMX)
        for url in ("/catalog/", "/inventory/"):
            html = self.client.get(url).content.decode()
            self.assertRegex(html, r'Caja<span class="sr-only"> abierta</span>')
            self.assertRegex(html, r'(?s)id="session-total".*?\$75\.00')

    def test_the_stand_in_is_gone(self):
        from importlib.util import find_spec
        self.assertIsNone(find_spec("apps.core.preview"))


class OfflineScreensTests(ViewTestCase):
    """CLAUDE.md §5-bis: Productos, Inventario, Caja and Reportes can be read without network (last copy)."""

    def test_service_worker_keeps_a_copy_of_every_screen(self):
        body = self.client.get("/pos/sw.js").content.decode()
        self.assertIn('const MODULOS = ["/pos/", "/catalog/", "/inventory/", "/reports/"];', body)
        self.assertIn('name="sgft-copia"', body)
        # No background refresh of pages: each request re-saves the session and would undo a ticket change made
        # meanwhile (Transferencia came back as efectivo in the CI).
        self.assertNotIn("guardar-pantallas", body)
        self.assertNotIn("guardar-pantallas", self.client.get("/static/pos/offline.js").content.decode())
        self.assertIn("setCatchHandler", body)

    def test_padlock_screens_are_marked_and_carry_the_notice(self):
        self.unlock()
        for name in ("catalog:dish_catalog", "inventory:ingredient_list", "reports:cash", "reports:reports"):
            html = self.client.get(reverse(name)).content.decode()
            self.assertRegex(html, r"<body[^>]*\sdata-sgft-candado[\s>]", name)
            self.assertIn('x-data="pantallaSinRed"', html, name)
            self.assertIn('aria-labelledby="offline-pin-title"', html, name)

    def test_nueva_venta_keeps_its_own_offline_mode(self):
        html = self.client.get(BUILDER).content.decode()
        self.assertNotRegex(html, r"<body[^>]*\sdata-sgft-candado")
        self.assertNotIn('x-data="pantallaSinRed"', html)
        self.assertIn('x-data="ventaSinRed"', html)

    def test_locked_menu_items_say_where_their_copy_is(self):
        html = self.client.get(BUILDER).content.decode()
        for name in ("catalog:dish_catalog", "inventory:ingredient_list", "reports:cash", "reports:reports"):
            self.assertIn(f'data-sgft-url="{reverse(name)}"', html, name)

    def test_without_a_session_there_is_no_offline_notice(self):
        self.assertNotIn("pantallaSinRed", self.client_class().get("/accounts/activate/").content.decode())

    def test_every_screen_has_unique_ids(self):
        self.unlock()
        for name in ("catalog:dish_catalog", "inventory:ingredient_list", "reports:cash", "reports:reports"):
            self.assertUniqueIds(self.client.get(reverse(name)))

    def test_no_template_comment_leaks_into_the_page(self):
        # {# … #} only works on one line; a multi-line one is printed as text at the top of every page.
        from pathlib import Path
        from django.conf import settings
        for template in Path(settings.BASE_DIR, "apps").glob("**/templates/**/*.html"):
            for number, line in enumerate(template.read_text(encoding="utf-8").splitlines(), 1):
                if "{#" in line:
                    self.assertIn("#}", line, f"{template}:{number}")
        self.assertNotIn("{#", self.client.get(BUILDER).content.decode())

