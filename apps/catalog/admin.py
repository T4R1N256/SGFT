from django.contrib import admin
from .models import Category, Dish, Ingredient, Recipe


class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", )
    search_fields = ("name",)


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name",)
    inlines = [RecipeInline]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "stock", "min_stock", "unit_cost")
    list_filter = ("unit",)
    search_fields = ("name",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("dish", "ingredient", "quantity")
    list_filter = ("dish", "ingredient")