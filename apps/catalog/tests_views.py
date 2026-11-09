"""
View and view–template contract tests for Productos (WBS 3.2.1–3.2.3; DEC-25). Owner: Tarín (DEC-31).

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

from apps.catalog.models import Category, Dish, Ingredient, Recipe, Units
from apps.core.mixins import UNLOCKED_BY_KEY, UNLOCKED_UNTIL_KEY

HTMX = {"HTTP_HX_REQUEST": "true"}
CATALOG, CREATE, ADD_LINE, NEW_INGREDIENT = "/catalog/", "/catalog/dishes/new/", "/catalog/recipe-lines/new/", \
    "/catalog/ingredients/new/"


def edit_url(dish):
    return f"/catalog/dishes/{dish.pk}/edit/"


def recipe_url(dish):
    return f"/catalog/dishes/{dish.pk}/recipe/"


class ViewTestCase(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.admin = users.create_user(username="dueno", password="x-9Lq!pr2", role="admin")
        self.cashier = users.create_user(username="caja", password="x-9Lq!pr3", role="cashier")
        self.client.force_login(self.cashier)
        self.unlock()
        self.burritos = Category.objects.create(name="Burritos", emoji="🌯")
        self.drinks = Category.objects.create(name="Bebidas", emoji="")
        self.tortilla = Ingredient.objects.create(name="Tortilla de harina", unit=Units.PIECE, stock=Decimal("50"),
                                                  min_stock=Decimal("20"), unit_cost=Decimal("2.00"))
        self.beef = Ingredient.objects.create(name="Carne asada", unit=Units.KG, stock=Decimal("2"),
                                              min_stock=Decimal("3"), unit_cost=Decimal("180.00"))
        self.coffee = Ingredient.objects.create(name="Café molido", unit=Units.KG, stock=Decimal("0"),
                                                min_stock=Decimal("0.5"), unit_cost=Decimal("250.00"))
        self.asada = Dish.objects.create(name="Burrito de asada", category=self.burritos, price=Decimal("75.00"),
                                         description="Carne asada y frijol.")
        Recipe.objects.create(dish=self.asada, ingredient=self.tortilla, quantity=Decimal("1"))
        Recipe.objects.create(dish=self.asada, ingredient=self.beef, quantity=Decimal("0.150"))
        self.bean = Dish.objects.create(name="Frijol con queso", category=self.burritos, price=Decimal("50.00"))
        Recipe.objects.create(dish=self.bean, ingredient=self.tortilla, quantity=Decimal("1"))
        self.coffee_dish = Dish.objects.create(name="Café de olla", category=self.drinks, price=Decimal("25.00"))
        Recipe.objects.create(dish=self.coffee_dish, ingredient=self.coffee, quantity=Decimal("0.020"))
        self.new_dish = Dish.objects.create(name="Chile relleno", category=self.burritos, price=Decimal("80.00"))
        self.hidden = Dish.objects.create(name="Tamal", category=self.burritos, price=Decimal("30.00"), is_active=False)

    def unlock(self):
        session = self.client.session
        session[UNLOCKED_UNTIL_KEY] = (timezone.now() + timedelta(minutes=30)).timestamp()
        session[UNLOCKED_BY_KEY] = self.admin.pk
        session.save()

    def valid_dish(self, **changes):
        return {"name": "Burrito de deshebrada", "category": str(self.burritos.pk), "price": "78.50",
                "description": "Con frijol.", "active": "on", **changes}

    def assertUniqueIds(self, response):
        ids = Counter(re.findall(r'\sid="([^"]+)"', response.content.decode()))
        repeated = [i for i, n in ids.items() if n > 1]
        self.assertEqual(repeated, [], f"ids repetidos: {repeated}")

    def assertStartsWithId(self, response, tag, dom_id):
        self.assertTrue(response.content.decode().lstrip().startswith(f'<{tag} id="{dom_id}"'),
                        "el id destino va en la raíz del fragmento")

    def card(self, html, dish):
        return html.split(f'id="catalog-dish-{dish.pk}"')[1].split("</article>")[0]


class AccessTests(ViewTestCase):
    def test_locked_asks_for_the_pin(self):
        self.client.session.flush()
        self.client.force_login(self.cashier)
        response = self.client.get(CATALOG)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "pin_required.html")
        response = self.client.post(CREATE, self.valid_dish(), **HTMX)
        self.assertEqual((response.status_code, response["HX-Retarget"]), (403, "#dialog"))
        self.assertFalse(Dish.objects.filter(name="Burrito de deshebrada").exists())

    def test_without_session_goes_to_activation(self):
        self.client.logout()
        self.assertEqual(self.client.get(CATALOG).status_code, 302)


class DishCatalogTests(ViewTestCase):
    def test_full_page_lists_every_dish_with_its_availability(self):
        response = self.client.get(CATALOG)
        self.assertTemplateUsed(response, "catalog/products.html")
        html = response.content.decode()
        self.assertEqual(html.count('id="catalog-dish-'), 5)
        self.assertIn("4 platillos activos", html)
        self.assertIn("Disponible", self.card(html, self.bean))
        self.assertIn("Pocas porciones", self.card(html, self.asada))  # beef at 2 kg with minimum 3
        self.assertIn("Agotado", self.card(html, self.coffee_dish))  # coffee at 0
        self.assertIn("Sin receta", self.card(html, self.new_dish))
        self.assertIn("Inactivo", self.card(html, self.hidden))
        self.assertIn("$75.00", self.card(html, self.asada))
        self.assertIn("🌯", self.card(html, self.asada))
        self.assertIn("B", self.card(html, self.coffee_dish))  # no emoji: the category's initial
        self.assertIn('id="dialog"', html)
        self.assertUniqueIds(response)

    def test_search_returns_only_the_grid(self):
        response = self.client.get(CATALOG, {"q": "café"}, **HTMX)
        self.assertTemplateUsed(response, "catalog/partials/dish_grid.html")
        self.assertTemplateNotUsed(response, "base.html")
        self.assertStartsWithId(response, "div", "dish-grid")
        html = response.content.decode()
        self.assertIn("Café de olla", html)
        self.assertNotIn("Burrito de asada", html)

    def test_search_without_results_shows_centered_message(self):
        self.assertIn("Agrega platillos para verlos", self.client.get(CATALOG, {"q": "pizza"}, **HTMX).content.decode())

    def test_card_buttons_open_dialogs(self):
        html = self.client.get(CATALOG).content.decode()
        self.assertIn(f'hx-get="{edit_url(self.asada)}"', html)
        self.assertIn(f'hx-get="{recipe_url(self.asada)}"', html)
        self.assertIn(f'hx-get="{CREATE}"', html.split('<header class="flex flex-wrap')[1].split("</header>")[0])


class DishFormTests(ViewTestCase):
    def test_create_dialog_lists_the_real_categories(self):
        response = self.client.get(CREATE, **HTMX)
        self.assertTemplateUsed(response, "catalog/partials/dish_form.html")
        html = response.content.decode()
        self.assertIn("Agregar platillo", html)
        self.assertIn(f'<option value="{self.burritos.pk}"', html)
        self.assertIn(f'<option value="{self.drinks.pk}"', html)

    def test_create_invalid_is_422_retargeted_with_field_errors(self):
        response = self.client.post(CREATE, {"name": "", "category": "999", "price": "abc"}, **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response["HX-Retarget"], "#dialog")
        html = response.content.decode()
        self.assertIn("Escribe el nombre del platillo.", html)
        self.assertIn("Elige una categoría.", html)
        self.assertIn("Escribe el precio con números", html)
        self.assertEqual(Dish.objects.count(), 5)

    def test_price_with_three_decimals_is_422(self):
        response = self.client.post(CREATE, self.valid_dish(price="10.505"), **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertIn("dos decimales", response.content.decode())

    def test_create_valid_saves_and_returns_the_grid(self):
        response = self.client.post(CREATE, self.valid_dish(price="$1,078.50"), **HTMX)
        self.assertStartsWithId(response, "div", "dish-grid")
        dish = Dish.objects.get(name="Burrito de deshebrada")
        self.assertEqual((dish.price, dish.category, dish.is_active), (Decimal("1078.50"), self.burritos, True))
        html = response.content.decode()
        self.assertIn('id="dialog" hx-swap-oob="true"', html)
        self.assertIn("Sin receta", self.card(html, dish))
        self.assertUniqueIds(response)

    def test_edit_dialog_is_prefilled(self):
        html = self.client.get(edit_url(self.asada), **HTMX).content.decode()
        self.assertIn("Editar platillo", html)
        self.assertIn('value="Burrito de asada"', html)
        self.assertIn('value="75.00"', html)
        self.assertRegex(html, rf'value="{self.burritos.pk}"\s+selected')

    def test_edit_valid_saves_and_returns_only_that_card(self):
        response = self.client.post(edit_url(self.asada), self.valid_dish(), **HTMX)
        self.assertStartsWithId(response, "article", f"catalog-dish-{self.asada.pk}")
        self.asada.refresh_from_db()
        self.assertEqual((self.asada.name, self.asada.price), ("Burrito de deshebrada", Decimal("78.50")))
        html = response.content.decode()
        self.assertIn("$78.50", html)
        self.assertIn('id="dialog" hx-swap-oob="true"', html)

    def test_unchecking_active_hides_the_dish_without_deleting_it(self):
        data = self.valid_dish()
        del data["active"]
        html = self.client.post(edit_url(self.asada), data, **HTMX).content.decode()
        self.asada.refresh_from_db()
        self.assertFalse(self.asada.is_active)
        self.assertIn("Inactivo", html)

    def test_edit_unknown_dish_is_404(self):
        self.assertEqual(self.client.get("/catalog/dishes/999/edit/", **HTMX).status_code, 404)


class RecipeTests(ViewTestCase):
    def test_recipe_dialog_lists_the_saved_lines_with_units(self):
        response = self.client.get(recipe_url(self.asada), **HTMX)
        self.assertTemplateUsed(response, "catalog/partials/recipe_form.html")
        html = response.content.decode()
        self.assertEqual(html.count(" data-line class="), 2)
        self.assertIn('value="0.15"', html)
        self.assertIn(">kg</span>", html)
        self.assertIn(f'hx-get="{ADD_LINE}?index=2"', html)
        self.assertUniqueIds(response)

    def test_add_line_returns_row_and_next_button_out_of_band(self):
        response = self.client.get(ADD_LINE, {"index": "4"}, **HTMX)
        self.assertStartsWithId(response, "div", "recipe-line-4")
        html = response.content.decode()
        self.assertIn('name="ingredient_4"', html)
        self.assertIn(f'data-unit="kg">Carne asada', html)
        self.assertIn('id="add-recipe-line" hx-swap-oob="true"', html)
        self.assertIn("index=5", html)
        self.assertIn('id="recipe-empty" hx-swap-oob="delete"', html)

    def test_duplicate_ingredient_and_bad_quantity_are_422_and_nothing_changes(self):
        data = {"ingredient_0": self.tortilla.pk, "quantity_0": "1",
                "ingredient_1": self.tortilla.pk, "quantity_1": "2",
                "ingredient_2": self.beef.pk, "quantity_2": "0"}
        response = self.client.post(recipe_url(self.asada), data, **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response["HX-Retarget"], "#dialog")
        html = response.content.decode()
        self.assertIn("Ese insumo ya está en la receta.", html)
        self.assertIn("La cantidad debe ser mayor que cero.", html)
        self.assertEqual(self.asada.recipes.count(), 2)

    def test_empty_recipe_is_422(self):
        response = self.client.post(recipe_url(self.asada), {}, **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertIn("Agrega al menos un insumo a la receta.", response.content.decode())

    def test_valid_recipe_replaces_the_old_one_and_refreshes_the_card(self):
        data = {"ingredient_0": self.tortilla.pk, "quantity_0": "1"}
        response = self.client.post(recipe_url(self.new_dish), data, **HTMX)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(self.new_dish.recipes.values_list("ingredient", "quantity")),
                         [(self.tortilla.pk, Decimal("1.000"))])
        html = response.content.decode()
        self.assertIn("Receta de Chile relleno guardada.", html)
        self.assertIn('id="dialog" hx-swap-oob="true"', html)
        self.assertIn(f'id="catalog-dish-{self.new_dish.pk}" hx-swap-oob="true"', html)
        self.assertIn("Disponible", html)


class IngredientCreateTests(ViewTestCase):
    """catalog:ingredient_create (3.2.2): opens from Inventario; on success it triggers «ingredient-created»."""

    VALID = {"name": "Aguacate", "unit": "kg", "min_stock": "1.5"}

    def test_dialog_lists_the_units_and_has_no_initial_stock(self):
        response = self.client.get(NEW_INGREDIENT, **HTMX)
        self.assertTemplateUsed(response, "catalog/partials/ingredient_form.html")
        html = response.content.decode()
        for unit in ("kg", "g", "L", "ml", "pzas"):
            self.assertIn(f'<option value="{unit}"', html)
        for name in ("name", "unit", "min_stock"):
            self.assertIn(f'name="{name}"', html)
        self.assertNotIn('name="initial_stock"', html)

    def test_invalid_is_422_retargeted_with_field_errors(self):
        response = self.client.post(NEW_INGREDIENT, {"name": "", "unit": "tazas", "min_stock": "x"}, **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response["HX-Retarget"], "#dialog")
        html = response.content.decode()
        for message in ("Escribe el nombre del insumo.", "Elige la unidad de medida.",
                        "Escribe el mínimo con números."):
            self.assertIn(message, html)

    def test_repeated_name_is_422_from_the_model(self):
        response = self.client.post(NEW_INGREDIENT, {**self.VALID, "name": "Carne asada"}, **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(Ingredient.objects.filter(name="Carne asada").count(), 1)

    def test_valid_saves_with_stock_zero_and_triggers_the_event(self):
        response = self.client.post(NEW_INGREDIENT, self.VALID, **HTMX)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Trigger"], "ingredient-created")
        ingredient = Ingredient.objects.get(name="Aguacate")
        self.assertEqual((ingredient.unit, ingredient.min_stock, ingredient.stock), ("kg", Decimal("1.500"), 0))
        html = response.content.decode()
        self.assertIn("Insumo «Aguacate» agregado.", html)
        self.assertIn('id="dialog" hx-swap-oob="true"', html)
