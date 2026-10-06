"""URL routes for apps.catalog (Productos screen). Names describe the action."""
from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("", views.dish_catalog, name="dish_catalog"),
    path("dishes/new/", views.dish_create, name="dish_create"),
    path("dishes/<int:dish_id>/edit/", views.dish_edit, name="dish_edit"),
    path("dishes/<int:dish_id>/recipe/", views.recipe_edit, name="recipe_edit"),
    path("recipe-lines/new/", views.add_recipe_line, name="add_recipe_line"),
    path("ingredients/new/", views.ingredient_create, name="ingredient_create"),
]
