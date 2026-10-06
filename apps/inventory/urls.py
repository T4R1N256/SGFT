"""URL routes for apps.inventory. Each package adds its views here; names describe the action."""
from django.urls import path

from . import views

app_name = "inventory"
urlpatterns = [
    path("", views.ingredient_list, name="ingredient_list"),
    path("purchases/new/", views.register_purchase, name="register_purchase"),
    path("waste/new/", views.register_waste, name="register_waste"),
]
