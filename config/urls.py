"""Root URLconf: includes each app's urls.py and sends the root to Nueva venta (estructura-y-flujo-datos-SGFT.md §1)."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # The device stays signed in as the cashier (DEC-34), so the root opens Nueva venta.
    path("", RedirectView.as_view(pattern_name="pos:order_builder", permanent=False), name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("pos/", include("apps.pos.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("reports/", include("apps.reports.urls")),
]
