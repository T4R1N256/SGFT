"""Unit tests for apps.catalog. Whoever implements a service writes its tests."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.catalog import services
from apps.catalog.models import Category, Dish, Ingredient, Recipe, Units


class CatalogServicesBase(TestCase):
    def setUp(self):
        self.burritos = Category.objects.create(name="Burritos")
        self.drinks = Category.objects.create(name="Bebidas")
        self.tortilla = services.create_ingredient("Tortilla de harina", Units.PIECE, unit_cost=Decimal("2.50"))
        self.beans = services.create_ingredient("Frijoles", Units.G, unit_cost=Decimal("0.04"))
        self.dish = services.create_dish("Burrito de frijol", self.burritos, Decimal("45.00"))


class DishServicesTests(CatalogServicesBase):
    """WBS 3.2.1 — platillos y precios."""

    def test_create_dish(self):
        self.assertEqual(Dish.objects.get(name="Burrito de frijol").price, Decimal("45.00"))
        self.assertTrue(self.dish.is_active)

    def test_negative_price_is_rejected(self):
        with self.assertRaises(ValidationError):
            services.create_dish("Gratis", self.burritos, Decimal("-1.00"))
        self.assertFalse(Dish.objects.filter(name="Gratis").exists())

    def test_price_with_three_decimals_is_rejected(self):
        with self.assertRaises(ValidationError):
            services.create_dish("Raro", self.burritos, Decimal("10.005"))

    def test_update_price_and_category(self):
        services.update_dish(self.dish, price=Decimal("50.00"), category=self.drinks)
        self.dish.refresh_from_db()
        self.assertEqual((self.dish.price, self.dish.category), (Decimal("50.00"), self.drinks))

    def test_update_rejects_unknown_fields(self):
        with self.assertRaises(ValueError):
            services.update_dish(self.dish, pk=99)

    def test_inactive_dish_leaves_the_menu_but_is_kept(self):
        services.set_dish_active(self.dish, False)
        self.assertNotIn(self.dish, services.active_dishes())
        self.assertTrue(Dish.objects.filter(pk=self.dish.pk).exists())

    def test_active_dishes_by_category_and_name(self):
        soda = services.create_dish("Refresco", self.drinks, Decimal("25.00"))
        asada = services.create_dish("Burrito de asada", self.burritos, Decimal("70.00"))
        self.assertEqual(list(services.active_dishes()), [soda, asada, self.dish])


class IngredientServicesTests(CatalogServicesBase):
    """WBS 3.2.2 — insumos con unidad, mínimo y costo."""

    def test_new_ingredient_starts_with_zero_stock(self):
        self.assertEqual(self.tortilla.stock, Decimal("0"))
        self.assertEqual(self.tortilla.unit, Units.PIECE)

    def test_unknown_unit_is_rejected(self):
        with self.assertRaises(ValidationError):
            services.create_ingredient("Sal", "tazas")

    def test_negative_minimum_is_rejected(self):
        with self.assertRaises(ValidationError):
            services.create_ingredient("Sal", Units.G, min_stock=Decimal("-1"))

    def test_duplicate_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            services.create_ingredient("Frijoles", Units.KG)

    def test_update_minimum_and_cost(self):
        services.update_ingredient(self.beans, min_stock=Decimal("500"), unit_cost=Decimal("0.05"))
        self.beans.refresh_from_db()
        self.assertEqual((self.beans.min_stock, self.beans.unit_cost), (Decimal("500"), Decimal("0.05")))

    def test_stock_cannot_be_set_here(self):
        with self.assertRaises(ValueError):
            services.update_ingredient(self.beans, stock=Decimal("100"))

    def test_unit_can_change_while_unused(self):
        services.update_ingredient(self.beans, unit=Units.KG)
        self.beans.refresh_from_db()
        self.assertEqual(self.beans.unit, Units.KG)

    def test_unit_cannot_change_once_in_a_recipe(self):
        services.set_recipe(self.dish, [(self.beans, Decimal("120"))])
        with self.assertRaises(ValidationError):
            services.update_ingredient(self.beans, unit=Units.KG)

    def test_unit_cannot_change_once_it_has_movements(self):
        user = get_user_model().objects.create_user(username="dueno", password="x-9Lq!pr2", role="admin")
        self.beans.movements.create(kind="purchase", quantity=Decimal("1000"), created_by=user)  # no import of inventory
        with self.assertRaises(ValidationError):
            services.update_ingredient(self.beans, unit=Units.KG)


class RecipeServicesTests(CatalogServicesBase):
    """WBS 3.2.3 — recetas y costo del platillo."""

    def test_set_recipe(self):
        services.set_recipe(self.dish, [(self.tortilla, Decimal("1")), (self.beans, Decimal("120"))])
        self.assertEqual(
            {(row.ingredient, row.quantity) for row in self.dish.recipes.all()},
            {(self.tortilla, Decimal("1")), (self.beans, Decimal("120"))},
        )

    def test_set_recipe_replaces_the_old_one(self):
        services.set_recipe(self.dish, [(self.tortilla, Decimal("1")), (self.beans, Decimal("120"))])
        services.set_recipe(self.dish, [(self.tortilla, Decimal("2"))])
        self.assertEqual(list(self.dish.recipes.values_list("ingredient__name", "quantity")),
                         [("Tortilla de harina", Decimal("2"))])

    def test_zero_quantity_keeps_the_old_recipe(self):
        services.set_recipe(self.dish, [(self.tortilla, Decimal("1"))])
        with self.assertRaises(ValidationError):
            services.set_recipe(self.dish, [(self.tortilla, Decimal("1")), (self.beans, Decimal("0"))])
        self.assertEqual(Recipe.objects.filter(dish=self.dish).count(), 1)

    def test_repeated_ingredient_is_rejected(self):
        with self.assertRaises(ValidationError):
            services.set_recipe(self.dish, [(self.beans, Decimal("1")), (self.beans, Decimal("2"))])

    def test_empty_recipe_is_rejected(self):
        with self.assertRaises(ValidationError):
            services.set_recipe(self.dish, [])

    def test_cost_and_margin(self):
        services.set_recipe(self.dish, [(self.tortilla, Decimal("1")), (self.beans, Decimal("120"))])
        self.assertEqual(services.dish_cost(self.dish), Decimal("7.30"))  # 2.50 + 120 × 0.04
        self.assertEqual(services.dish_margin(self.dish), Decimal("37.70"))

    def test_dish_without_recipe_costs_zero(self):
        self.assertEqual(services.dish_cost(self.dish), Decimal("0.00"))