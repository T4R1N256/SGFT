"""URL routes for apps.reports. Each package adds its views here; names describe the action."""
from django.urls import path

from . import views

app_name = "reports"
urlpatterns = [
    path("", views.reports, name="reports"),
    path("cash/", views.cash, name="cash"),
    path("daily-sales.pdf", views.export_daily_sales_pdf, name="export_daily_sales_pdf"),
]
