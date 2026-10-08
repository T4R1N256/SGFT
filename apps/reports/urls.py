"""URL routes for apps.reports. Each package adds its views here; names describe the action."""
from django.urls import path

from . import views

app_name = "reports"
urlpatterns = [
    path("cash/", views.cash, name="cash"),
]
