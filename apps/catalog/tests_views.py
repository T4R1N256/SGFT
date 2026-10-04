"""
View and view–template contract tests for Productos (WBS 3.2.1, 3.2.3; DEC-25). Owner: Tarín (DEC-31).

The views are called directly with RequestFactory, so the tests do not depend on urls.py (pending, see
rutas-pendientes.md). HTMX requests are simulated with the HX-Request header and django-htmx's HtmxDetails.
"""
import re
from collections import Counter

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase
from django_htmx.middleware import HtmxDetails

from apps.catalog import views


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


VALID_DISH = {"name": "Burrito de deshebrada", "category": "burritos", "price": "78.50", "description": "Con frijol.", "active": "on"}


class DishCatalogTests(ViewTestCase):
    def test_full_page_shows_nine_dishes_and_add_tile(self):
        with self.assertTemplateUsed("catalog/products.html"), self.assertTemplateUsed("base.html"):
            response = self.call(views.dish_catalog)
        html = response.content.decode()
        self.assertEqual(html.count('id="catalog-dish-'), 9)
        self.assertIn("9 platillos activos", html)
        self.assertIn("Pocas porciones", html)
        self.assertIn('id="dialog"', html)
        self.assertNotIn("Ordenar", html)
        self.assertUniqueIds(response)

    def test_search_returns_only_the_grid(self):
        with self.assertTemplateUsed("catalog/partials/dish_grid.html"), self.assertTemplateNotUsed("base.html"):
            response = self.call(views.dish_catalog, htmx=True, data={"q": "café"})
        self.assertStartsWithId(response, "div", "dish-grid")
        html = response.content.decode()
        self.assertIn("Café de olla", html)
        self.assertNotIn("Burrito de asada", html)

    def test_search_without_results_shows_centered_message(self):
        response = self.call(views.dish_catalog, htmx=True, data={"q": "pizza"})
        self.assertIn("Agrega platillos para verlos", response.content.decode())

    def test_card_buttons_open_dialogs(self):
        html = self.call(views.dish_catalog).content.decode()
        self.assertGreaterEqual(html.count('hx-target="#dialog"'), 19)  # 9 × (Receta, Editar) + tile


    def test_add_button_is_in_the_header_and_the_tile_is_gone(self):
        html = self.call(views.dish_catalog).content.decode()
        header = html.split('<header class="flex flex-wrap')[1].split("</header>")[0]
        self.assertIn("Agregar platillo", header)
        self.assertNotIn("border-dashed", html.split('id="dish-grid"')[1])


class DishFormTests(ViewTestCase):
    def test_create_dialog(self):
        with self.assertTemplateUsed("catalog/partials/dish_form.html"):
            response = self.call(views.dish_create, htmx=True)
        html = response.content.decode()
        self.assertIn("Agregar platillo", html)
        for name in ("name", "category", "price", "description", "active"):
            self.assertIn(f'name="{name}"', html)

    def test_form_has_no_ingredient_list(self):
        html = self.call(views.dish_create, htmx=True).content.decode()
        self.assertNotIn("Insumos que consume", html)
        self.assertNotIn('name="qty_', html)

    def test_create_invalid_is_422_retargeted_with_field_errors(self):
        response = self.call(views.dish_create, method="post", htmx=True, data={"name": "", "category": "x", "price": "abc"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response["HX-Retarget"], "#dialog")
        html = response.content.decode()
        self.assertIn("Escribe el nombre del platillo.", html)
        self.assertIn("Elige una categoría.", html)
        self.assertIn("Escribe el precio con números", html)

    def test_create_valid_returns_grid_and_closes_dialog(self):
        response = self.call(views.dish_create, method="post", htmx=True, data=VALID_DISH)
        self.assertStartsWithId(response, "div", "dish-grid")
        self.assertIn('id="dialog" hx-swap-oob="true"', response.content.decode())
        self.assertUniqueIds(response)

    def test_edit_dialog_is_prefilled(self):
        html = self.call(views.dish_edit, htmx=True, dish_id=1).content.decode()
        self.assertIn("Editar platillo", html)
        self.assertIn('value="Burrito de asada"', html)
        self.assertIn('value="75.00"', html)
        self.assertRegex(html, r'value="burritos"\s+selected')

    def test_edit_valid_returns_only_that_card(self):
        response = self.call(views.dish_edit, method="post", htmx=True, dish_id=1, data=VALID_DISH)
        self.assertStartsWithId(response, "article", "catalog-dish-1")
        html = response.content.decode()
        self.assertIn("Burrito de deshebrada", html)
        self.assertIn("$78.50", html)
        self.assertIn('id="dialog" hx-swap-oob="true"', html)

    def test_edit_unknown_dish_is_404(self):
        self.assertEqual(self.call(views.dish_edit, htmx=True, dish_id=999).status_code, 404)


class RecipeTests(ViewTestCase):
    def test_recipe_dialog_lists_lines_with_units(self):
        with self.assertTemplateUsed("catalog/partials/recipe_form.html"):
            response = self.call(views.recipe_edit, htmx=True, dish_id=1)
        html = response.content.decode()
        self.assertEqual(html.count(" data-line class="), 4)
        self.assertIn("Burrito de asada", html)
        self.assertIn('hx-get="#?index=4"', html)
        self.assertUniqueIds(response)

    def test_add_line_returns_row_and_next_button_out_of_band(self):
        response = self.call(views.add_recipe_line, htmx=True, data={"index": "4"})
        html = response.content.decode()
        self.assertStartsWithId(response, "div", "recipe-line-4")
        self.assertIn('name="ingredient_4"', html)
        self.assertIn('id="add-recipe-line" hx-swap-oob="true"', html)
        self.assertIn("index=5", html)
        self.assertIn('id="recipe-empty" hx-swap-oob="delete"', html)

    def test_duplicate_ingredient_and_bad_quantity_are_422(self):
        data = {"ingredient_0": "1", "quantity_0": "1", "ingredient_1": "1", "quantity_1": "2", "ingredient_2": "2", "quantity_2": "0"}
        response = self.call(views.recipe_edit, method="post", htmx=True, dish_id=1, data=data)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response["HX-Retarget"], "#dialog")
        html = response.content.decode()
        self.assertIn("Ese insumo ya está en la receta.", html)
        self.assertIn("La cantidad debe ser mayor que cero.", html)

    def test_empty_recipe_is_422(self):
        response = self.call(views.recipe_edit, method="post", htmx=True, dish_id=1, data={})
        self.assertEqual(response.status_code, 422)
        self.assertIn("Agrega al menos un insumo a la receta.", response.content.decode())

    def test_valid_recipe_shows_success_and_closes_dialog(self):
        data = {"ingredient_0": "1", "quantity_0": "1", "ingredient_1": "2", "quantity_1": "0.15"}
        html = self.call(views.recipe_edit, method="post", htmx=True, dish_id=1, data=data).content.decode()
        self.assertIn("Receta de Burrito de asada guardada.", html)
        self.assertIn('id="dialog" hx-swap-oob="true"', html)


class IngredientCreateTests(ViewTestCase):
    """catalog:ingredient_create (3.2.2): the dialog opens from Inventario; on success it triggers «ingredient-created»."""

    VALID = {"name": "Aguacate", "unit": "kg", "initial_stock": "3", "initial_cost": "180.00", "min_stock": "1"}

    def test_dialog_lists_the_agreed_units(self):
        with self.assertTemplateUsed("catalog/partials/ingredient_form.html"):
            html = self.call(views.ingredient_create, htmx=True).content.decode()
        self.assertIn("Agregar insumo", html)
        for unit in ("kg", "g", "L", "ml", "pzas"):
            self.assertIn(f'<option value="{unit}"', html)
        for name in ("name", "unit", "initial_stock", "initial_cost", "min_stock"):
            self.assertIn(f'name="{name}"', html)

    def test_invalid_is_422_retargeted_with_field_errors(self):
        response = self.call(views.ingredient_create, method="post", htmx=True,
                             data={"name": "", "unit": "tazas", "initial_stock": "-1", "min_stock": "x"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response["HX-Retarget"], "#dialog")
        html = response.content.decode()
        for message in ("Escribe el nombre del insumo.", "Elige la unidad de medida.", "La existencia no puede ser negativa.",
                        "Escribe el mínimo con números."):
            self.assertIn(message, html)

    def test_cost_is_required_only_with_initial_stock(self):
        without_cost = {**self.VALID, "initial_cost": ""}
        response = self.call(views.ingredient_create, method="post", htmx=True, data=without_cost)
        self.assertEqual(response.status_code, 422)
        self.assertIn("Escribe el costo total de la existencia inicial.", response.content.decode())
        no_stock = {**without_cost, "initial_stock": "0"}
        self.assertEqual(self.call(views.ingredient_create, method="post", htmx=True, data=no_stock).status_code, 200)

    def test_valid_shows_success_closes_dialog_and_triggers_event(self):
        response = self.call(views.ingredient_create, method="post", htmx=True, data=self.VALID)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Trigger"], "ingredient-created")
        html = response.content.decode()
        self.assertIn("Insumo «Aguacate» agregado.", html)
        self.assertIn('id="dialog" hx-swap-oob="true"', html)
