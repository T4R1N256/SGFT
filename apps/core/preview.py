"""
TEMPORARY stand-in for the cash session and the screens' shell, merged to main on purpose (PR #44) so the team can
walk through every screen. The admin PIN is no longer simulated: is_unlocked asks the real padlock of
apps/core/mixins.py, which accounts.views.admin_pin opens with an Administrator's PIN (WBS 3.1.2).

Remove it, with every «preview.» call in the views, once the real pieces exist (rutas-pendientes.md):
  - the role/PIN mixin of apps/core/mixins.py (Jesús, J3), which replaces require_admin_pin;
  - the shell context processor of apps/core (Jesús, J2), which replaces apply_to_shell and each app's _shell_context;
  - the cash session services (Jared and Jesús), which replace is_cash_open and set_cash_open.

State lives in the Django session. Without a session (views called with RequestFactory in the tests) everything
stays unlocked and the cash open, as in the contract drafts, so the view tests keep their meaning.
"""
from functools import wraps
from urllib.parse import urlencode

from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse

from apps.core.mixins import is_admin_unlocked

_CASH_OPEN = "preview_cash_session_open"


def _session(request):
    return getattr(request, "session", None)


def is_unlocked(request):
    return True if _session(request) is None else is_admin_unlocked(request)


def is_cash_open(request):
    session = _session(request)
    return True if session is None else session.get(_CASH_OPEN, False)


def set_cash_open(request, value):
    if _session(request) is not None:
        request.session[_CASH_OPEN] = value


def pin_url(module_label, next_url):
    return reverse("accounts:admin_pin") + "?" + urlencode({"module": module_label, "next": next_url})


def pin_dialog_context(module_label, next_url, error=""):
    # The module travels in the query string so a 422 keeps «Para entrar a …».
    return {"post_url": reverse("accounts:admin_pin") + "?" + urlencode({"module": module_label}), "hx_target": "#dialog", "hx_swap": "innerHTML",
            "module_label": module_label, "next_url": next_url, "error": error}


def lock_menu(request, modules):
    """While locked, modules with a padlock open the PIN dialog (pin_url) instead of navigating."""
    locked = not is_unlocked(request)
    return [{**m, "pin_url": pin_url(m["label"], m["url"]) if locked and m["requires_pin"] else ""} for m in modules]


def apply_to_shell(request, context):
    """Menu with the PIN dialog and the cash state of the top bar, on top of a view's draft shell context."""
    context["nav_modules"] = lock_menu(request, context["nav_modules"])
    context["cash_session_open"] = is_cash_open(request)
    if not context["cash_session_open"]:
        context["session_total"] = None
    return context


def require_admin_pin(module_label, shell):
    """
    Locked module: a full page gets pin_required.html (403) with the PIN dialog already open; an HTMX request gets
    the dialog in #dialog (403, HX-Retarget). shell(request) returns the menu and top bar context of the module.
    """
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if is_unlocked(request):
                return view(request, *args, **kwargs)
            if getattr(request, "htmx", False):
                next_url = request.headers.get("HX-Current-URL") or request.get_full_path()
                response = render(request, "components/pin_dialog.html", pin_dialog_context(module_label, next_url),
                                  status=403)
                response["HX-Retarget"] = "#dialog"
                response["HX-Reswap"] = "innerHTML"
                return response
            next_url = request.get_full_path()
            context = {**shell(request), "module_label": module_label, "pin_url": pin_url(module_label, next_url),
                       "pin_dialog": render_to_string("components/pin_dialog.html",
                                                      pin_dialog_context(module_label, next_url), request)}
            return render(request, "pin_required.html", context, status=403)
        return wrapped
    return decorator
