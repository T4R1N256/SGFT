"""
Authorization for every view (WBS 3.1.3): role checks and the admin PIN padlock. Owner: Jesús; each owner of a
views.py applies these decorators, only Jesús modifies them. Hiding a button is not access control.

The device keeps a permanent cashier session (DEC-34). The modules with a padlock (Productos, Inventario, Caja,
Reportes, opening and closing the till) ask for an Administrator's PIN and stay unlocked for 30 minutes (DEC-32).
The unlock lives in the Django session under two keys, so whatever is authorized with the PIN is recorded under
that Administrator: admin_unlocked_until (POSIX timestamp) and admin_unlocked_by (user pk).

core depends on no other app: the user model is reached through get_user_model().
"""
from datetime import timedelta
from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import render, resolve_url
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

ADMIN_UNLOCK_MINUTES = 30
UNLOCKED_UNTIL_KEY = "admin_unlocked_until"
UNLOCKED_BY_KEY = "admin_unlocked_by"
ADMIN = "admin"
CASHIER = "cashier"


# --- Admin PIN unlock (session) ---------------------------------------------------------------

def unlock_admin(request, admin):
    """Opens the padlock for 30 minutes on behalf of admin. Called by the PIN view after verify_admin_pin()."""
    request.session[UNLOCKED_UNTIL_KEY] = (timezone.now() + timedelta(minutes=ADMIN_UNLOCK_MINUTES)).timestamp()
    request.session[UNLOCKED_BY_KEY] = admin.pk


def lock_admin(request):
    request.session.pop(UNLOCKED_UNTIL_KEY, None)
    request.session.pop(UNLOCKED_BY_KEY, None)


def unlocked_admin(request):
    """The Administrator who unlocked the padlock, or None if it expired or that account is no longer an active admin."""
    session = getattr(request, "session", None)
    if session is None:
        return None
    until = session.get(UNLOCKED_UNTIL_KEY)
    if not until or timezone.now().timestamp() >= until:
        return None
    return get_user_model().objects.filter(pk=session.get(UNLOCKED_BY_KEY), is_active=True, role=ADMIN).first()


def is_admin_unlocked(request):
    return unlocked_admin(request) is not None


# --- PIN dialog -------------------------------------------------------------------------------

def pin_url(module_label, next_url):
    """GET of the PIN dialog (accounts:admin_pin) for a module, coming back to next_url once unlocked."""
    return reverse("accounts:admin_pin") + "?" + urlencode({"module": module_label, "next": next_url})


def pin_dialog_context(module_label, next_url, error=""):
    # The module travels in the query string so a 422 keeps «Para entrar a …».
    return {"post_url": reverse("accounts:admin_pin") + "?" + urlencode({"module": module_label}),
            "hx_target": "#dialog", "hx_swap": "innerHTML", "module_label": module_label, "next_url": next_url,
            "error": error}


def _retarget_dialog(response):
    response["HX-Retarget"] = "#dialog"
    response["HX-Reswap"] = "innerHTML"
    return response


# --- Decorators -------------------------------------------------------------------------------

def _not_authenticated(request):
    """No session: the device is not activated. HTMX gets 401 plus HX-Redirect; a full page, a redirect."""
    if getattr(request, "htmx", False):
        response = HttpResponse("Activa el dispositivo para continuar.", status=401)
        response["HX-Redirect"] = _login_url()
        return response
    return redirect_to_login(request.get_full_path(), _login_url())


def _login_url():
    # LOGIN_URL names the activation view (WBS 3.1.2); until it exists, Django Admin's login stands in.
    try:
        return resolve_url(settings.LOGIN_URL)
    except NoReverseMatch:
        return reverse("admin:login")


def role_required(*roles):
    """
    Only active users with one of roles. Without a session → activation (see _not_authenticated); with another role
    → 403 with an alert. role_required() with no arguments accepts both roles.
    """
    allowed = set(roles or (ADMIN, CASHIER))

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return _not_authenticated(request)
            if not user.is_active or user.role not in allowed:
                response = render(request, "components/alert.html",
                                  {"message": "Tu cuenta no tiene permiso para esta acción."}, status=403)
                if getattr(request, "htmx", False):
                    response["HX-Retarget"] = "#messages"
                    response["HX-Reswap"] = "afterbegin"
                return response
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def admin_pin_required(module_label):
    """
    Module with a padlock: needs a session (any role) and the admin PIN given less than 30 minutes ago.
    Locked, a full page gets pin_required.html (403) with the PIN dialog already open; an HTMX request gets the
    dialog in #dialog (403, HX-Retarget). The menu and top bar come from apps.core.context_processors.shell.
    The view can read who authorized it with unlocked_admin(request).
    """
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return _not_authenticated(request)
            if is_admin_unlocked(request):
                return view(request, *args, **kwargs)
            if getattr(request, "htmx", False):
                next_url = request.headers.get("HX-Current-URL") or request.get_full_path()
                return _retarget_dialog(render(request, "components/pin_dialog.html",
                                               pin_dialog_context(module_label, next_url), status=403))
            next_url = request.get_full_path()
            context = {"module_label": module_label, "pin_url": pin_url(module_label, next_url),
                       "pin_dialog": render_to_string("components/pin_dialog.html",
                                                      pin_dialog_context(module_label, next_url), request)}
            return render(request, "pin_required.html", context, status=403)
        return wrapped
    return decorator


class RoleRequiredMixin:
    """Class-based views: allowed_roles = ("admin",). Same behavior as role_required."""
    allowed_roles = (ADMIN, CASHIER)

    def dispatch(self, request, *args, **kwargs):
        return role_required(*self.allowed_roles)(super().dispatch)(request, *args, **kwargs)


class AdminPinRequiredMixin:
    """Class-based views: module_label = "Inventario". Same behavior as admin_pin_required."""
    module_label = ""

    def dispatch(self, request, *args, **kwargs):
        return admin_pin_required(self.module_label)(super().dispatch)(request, *args, **kwargs)
