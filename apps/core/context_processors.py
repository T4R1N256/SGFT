"""
Shell context for base.html (menu and top bar) on every page, so views stop building it by hand. Owner: Jesús.
A view that passes one of these keys overrides it. The cash state (cash_session_open, session_total) is not here:
core depends on no other app, so the pos views keep supplying it.
"""
from django.urls import NoReverseMatch, reverse

from .mixins import is_admin_unlocked, pin_url

# key, label, icon, URL name, padlock. reverse() by name is not an import, so core does not depend on the apps.
MODULES = [
    ("pos", "Nueva Venta", "shopping-cart", "pos:order_builder", False),
    ("products", "Productos", "package", "catalog:dish_catalog", True),
    ("inventory", "Inventario", "clipboard-list", "inventory:ingredient_list", True),
    ("cash", "Caja", "wallet", "reports:cash", True),
    ("reports", "Reportes", "chart-column", "reports:reports", True),
]
_ACTIVE_BY_NAMESPACE = {"pos": "pos", "catalog": "products", "inventory": "inventory", "reports": "reports"}


def _url(name):
    try:
        return reverse(name)
    except NoReverseMatch:
        return "#"


def _active_module(request):
    match = getattr(request, "resolver_match", None)
    if match is None:
        return ""
    if match.namespace == "reports" and match.url_name and match.url_name.startswith("cash"):
        return "cash"
    return _ACTIVE_BY_NAMESPACE.get(match.namespace, "")


def _initials(user):
    if not user.is_authenticated:
        return ""
    name = user.get_full_name() or user.get_username()
    return "".join(part[0] for part in name.split()[:2]).upper()


def nav_modules(request, unlocked):
    """Menu entries; while the padlock is closed, modules with a padlock open the PIN dialog (pin_url)."""
    locked = not unlocked
    modules = []
    for key, label, icon, url_name, requires_pin in MODULES:
        url = _url(url_name)
        modules.append({"key": key, "label": label, "icon": icon, "url": url, "requires_pin": requires_pin,
                        "pin_url": pin_url(label, url) if locked and requires_pin else ""})
    return modules


def shell(request):
    unlocked = is_admin_unlocked(request)
    return {
        "nav_modules": nav_modules(request, unlocked),
        "active_module": _active_module(request),
        "admin_unlocked": unlocked,
        "sync_pending": 0,  # without network static/pos/ updates the counter (3.4.3)
        "user_initials": _initials(request.user) if hasattr(request, "user") else "",
    }
