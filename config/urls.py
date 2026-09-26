"""Root URLconf: only includes each app's urls.py (estructura-y-flujo-datos-SGFT.md §1)."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("pos/", include("apps.pos.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("reports/", include("apps.reports.urls")),
]
