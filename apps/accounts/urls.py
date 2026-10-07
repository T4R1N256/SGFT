"""URL routes for apps.accounts. Each package adds its views here; names describe the action."""
from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("pin/", views.admin_pin, name="admin_pin"),  # stand-in for the integration branch only
]
