"""
View and view–template contract tests for Nueva Venta (WBS 3.3.1, 3.3.5, 3.5.1). Owner: Tarín (DEC-31).

The views are called directly with RequestFactory, so the tests do not depend on urls.py (pending, see
rutas-pendientes.md). HTMX requests are simulated with the HX-Request header and django-htmx's HtmxDetails.
"""
import re
from collections import Counter

from django.contrib.auth.models import AnonymousUser
from unittest import skipUnless

from django.test import RequestFactory, SimpleTestCase
from django_htmx.middleware import HtmxDetails

from apps.pos import views


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


class OrderBuilderTests(ViewTestCase):
    def test_full_page_renders_sale_area_inside_base(self):
        with self.assertTemplateUsed("pos/order_builder.html"), self.assertTemplateUsed("base.html"):
            response = self.call(views.order_builder)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('id="sale-area"', html)
        self.assertIn('id="order-summary"', html)
        self.assertIn('id="dialog"', html)
        self.assertIn("$480.00", html)
        self.assertIn("Alerta stock", html)
        self.assertUniqueIds(response)

    def test_htmx_returns_only_the_fragment(self):
        with self.assertTemplateUsed("pos/partials/sale_area.html"), self.assertTemplateNotUsed("base.html"):
            response = self.call(views.order_builder, htmx=True)
        html = response.content.decode()
        self.assertTrue(html.lstrip().startswith('<div id="sale-area"'), "el id destino va en la raíz del fragmento")
        self.assertNotIn("<html", html)

    def test_closed_cash_session_disables_content_and_offers_open(self):
        response = self.call(views.order_builder, data={"estado": "caja-cerrada"})
        html = response.content.decode()
        self.assertIn("La caja está cerrada", html)
        self.assertIn("inert", html)
        self.assertRegex(html, r'Caja<span class="sr-only"> cerrada</span>')
        self.assertNotIn("Alerta stock", html)

    def test_no_sort_or_filter_buttons(self):
        html = self.call(views.order_builder).content.decode()
        self.assertNotIn(">Ordenar", html.replace("\n", ""))
        self.assertNotIn("Filtros", html)

    def test_quantity_badges_sit_on_the_thumbnails(self):
        html = self.call(views.order_builder).content.decode()
        self.assertEqual(html.count("sgft-dish-card__qty--thumb"), 6)
        self.assertEqual(html.count("sgft-dish-card__qty--line"), 6)
        self.assertIn('class="sgft-qty-modal"', html)

    def test_empty_ticket_disables_confirm(self):
        response = self.call(views.order_builder, data={"estado": "ticket-vacio"})
        html = response.content.decode()
        self.assertIn("Toca un platillo para agregarlo", html)
        self.assertRegex(html, r'(?s)disabled aria-disabled="true">\s*<span[^>]*>.*?</span>\s*Confirmar compra')


class DishListTests(ViewTestCase):
    def test_without_htmx_redirects(self):
        response = self.call(views.dish_list)
        self.assertEqual(response.status_code, 302)

    def test_filters_by_category_and_marks_active_chip_out_of_band(self):
        with self.assertTemplateUsed("pos/partials/dish_list.html"):
            response = self.call(views.dish_list, htmx=True, data={"category": "bebidas"})
        html = response.content.decode()
        self.assertIn("Café de olla", html)
        self.assertNotIn("Burrito de asada", html)
        self.assertIn('id="category-chips" hx-swap-oob="true"', html)
        self.assertRegex(html, r'aria-pressed="true"[^>]*>\s*Bebidas')
        self.assertUniqueIds(response)

    def test_category_without_dishes_shows_centered_message(self):
        response = self.call(views.dish_list, htmx=True, data={"category": "guisados"})
        self.assertIn("Agrega platillos para verlos", response.content.decode())


class OrderSummaryTests(ViewTestCase):
    def test_add_item_returns_ticket_and_dish_card_out_of_band(self):
        with self.assertTemplateUsed("pos/partials/order_summary.html"):
            response = self.call(views.add_item, method="post", htmx=True, dish_id=1)
        html = response.content.decode()
        self.assertTrue(html.lstrip().startswith('<aside id="order-summary"'), "el id destino va en la raíz del fragmento")
        self.assertIn('id="dish-1" hx-swap-oob="true"', html)
        self.assertUniqueIds(response)

    def test_remove_item_and_remove_dish(self):
        for view, kwargs in ((views.remove_item, {"line_id": 11}), (views.remove_dish, {"dish_id": 1})):
            response = self.call(view, method="post", htmx=True, **kwargs)
            self.assertEqual(response.status_code, 200)
            self.assertIn('id="order-summary"', response.content.decode())

    def test_payment_method_selected_by_server(self):
        response = self.call(views.set_payment_method, method="post", htmx=True, data={"method": "transferencia"})
        self.assertRegex(response.content.decode(), r'(?s)sgft-btn--seleccionado.*?value="transferencia"|value="transferencia".*?sgft-btn--seleccionado')

    def test_invalid_payment_method_is_retargeted_to_messages(self):
        response = self.call(views.set_payment_method, method="post", htmx=True, data={"method": "tarjeta"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response["HX-Retarget"], "#messages")
        self.assertIn("efectivo o transferencia", response.content.decode())

    def test_confirm_sale_empties_ticket_and_updates_shell_out_of_band(self):
        response = self.call(views.confirm_sale, method="post", htmx=True)
        html = response.content.decode()
        self.assertIn("Toca un platillo para agregarlo", html)
        self.assertIn('id="session-total" hx-swap-oob="true"', html)
        self.assertIn("$5,330.00", html)
        self.assertIn('id="dish-list" hx-swap-oob="true"', html)
        self.assertNotIn("sgft-dish-card__qty", html)
        self.assertUniqueIds(response)


class OpenSessionTests(ViewTestCase):
    def test_get_returns_dialog_with_six_pin_boxes(self):
        with self.assertTemplateUsed("pos/partials/open_cash_session.html"):
            response = self.call(views.open_session, htmx=True)
        self.assertEqual(response.content.decode().count('name="pin"'), 6)

    def test_short_pin_is_422_retargeted_to_dialog(self):
        response = self.call(views.open_session, method="post", htmx=True,
                             data={"pin": ["1", "2", "3"], "opening_amount": "500"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response["HX-Retarget"], "#dialog")
        self.assertIn("6 dígitos", response.content.decode())

    def test_valid_open_returns_sale_area_and_updates_cash_status(self):
        response = self.call(views.open_session, method="post", htmx=True,
                             data={"pin": list("123456"), "opening_amount": "500"})
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="cash-status" hx-swap-oob="true"', html)
        self.assertRegex(html, r'Caja<span class="sr-only"> abierta</span>')
        self.assertIn('id="dialog" hx-swap-oob="true"', html)
        self.assertUniqueIds(response)


def _template_exists(name):
    from django.template import TemplateDoesNotExist
    from django.template.loader import get_template
    try:
        get_template(name)
        return True
    except TemplateDoesNotExist:
        return False


CLOSE_TEMPLATE = "pos/partials/cash_session_close.html"


class CloseSessionTests(ViewTestCase):
    """pos:close_session (3.5.7). Its fragment is Yahir's (DEC-31): the tests that render it wait for that template."""

    def post_close(self, data):
        from django.contrib.messages.storage.cookie import CookieStorage
        request = self.factory.post("/", data, HTTP_HX_REQUEST="true")
        request.user = AnonymousUser()
        request.htmx = HtmxDetails(request)
        request._messages = CookieStorage(request)
        return views.close_session(request), request

    def test_valid_close_redirects_to_closed_sale_screen_with_message(self):
        response, request = self.post_close({"closing_amount": "3,600.00"})
        self.assertEqual(response.status_code, 204)
        self.assertTrue(response["HX-Redirect"].endswith("?estado=caja-cerrada"))
        self.assertEqual([m.message for m in request._messages], ["Caja cerrada. El corte del turno se generó con las ventas sincronizadas."])

    @skipUnless(_template_exists(CLOSE_TEMPLATE), "falta la plantilla de Yahir: " + CLOSE_TEMPLATE)
    def test_get_returns_dialog_with_expected_amount(self):
        response = self.call(views.close_session, htmx=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("3,620.00", response.content.decode())

    @skipUnless(_template_exists(CLOSE_TEMPLATE), "falta la plantilla de Yahir: " + CLOSE_TEMPLATE)
    def test_pending_operations_are_409_in_the_dialog(self):
        response, _ = self.post_close({"closing_amount": "3600", "estado": "pendientes"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response["HX-Retarget"], "#dialog")
        self.assertIn("Faltan 2 operaciones por sincronizar", response.content.decode())

    @skipUnless(_template_exists(CLOSE_TEMPLATE), "falta la plantilla de Yahir: " + CLOSE_TEMPLATE)
    def test_invalid_amount_is_422_in_the_dialog(self):
        response, _ = self.post_close({"closing_amount": "abc"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("Escribe el efectivo contado", response.content.decode())
