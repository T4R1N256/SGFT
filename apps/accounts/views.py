"""
Access views (WBS 3.1.2): device activation and the admin PIN dialog. Owner: Yahir.

There is no login page (DEC-34). The device is activated once with an Administrator's PIN and keeps a permanent
session of the cashier account; the modules with a padlock ask for the PIN again and stay unlocked 30 minutes.
The rules (which PIN is valid, the attempt limit) live in apps.accounts.services; the padlock in apps.core.mixins.
"""
from urllib.parse import urlencode

from django.contrib.auth import login
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from apps.accounts import services
from apps.accounts.models import is_pin
from apps.core.mixins import pin_dialog_context, role_required, unlock_admin

INCOMPLETE_PIN = "Escribe los 6 dígitos del PIN."
NO_CASHIER = "No hay una cuenta de cajero activa. Pide al administrador que la cree en Django Admin."


def _safe_next(request, default):
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                                    require_https=request.is_secure()):
        return next_url
    return default


def _done(request, next_url):
    """HTMX gets 204 + HX-Redirect; a normal form, a redirect."""
    if request.htmx:
        response = HttpResponse(status=204)
        response["HX-Redirect"] = next_url
        return response
    return redirect(next_url)


def _dialog_error(request, template, context):
    response = render(request, template, context, status=422)
    response["HX-Retarget"] = "#dialog"
    response["HX-Reswap"] = "innerHTML"
    return response


def _pin_error(pin):
    """Checks the PIN with the service; returns the user or the message for the dialog."""
    try:
        return services.verify_admin_pin(pin), ""
    except services.InvalidPinError as error:  # PinLockedError too: its message says how many minutes are left
        return None, str(error)


@require_http_methods(["GET", "POST"])
def activate_device(request):
    """
    CONTRATO VISTA–PLANTILLA — Activar este dispositivo (WBS 3.1.2, DEC-34)
    URL         : /accounts/activate/ (accounts:activate_device; es el LOGIN_URL)
    Roles       : sin sesión. Con sesión, GET redirige a next (o a Nueva venta) y POST responde 409.
    Plantillas  : GET normal → accounts/activate_device.html (página sin menú ni barra superior, con el diálogo
                  abierto) · HTMX → accounts/partials/activate_dialog.html [fragmento, en #dialog]
    Contexto    : post_url, hx_target, hx_swap, next_url, error; la página además activate_url
    hx-target   : #dialog (innerHTML)
    Respuestas  : POST con el PIN de un Administrador activo → inicia la sesión del cajero; 204 + HX-Redirect a
                  next (o redirección sin HTMX) · PIN incompleto, incorrecto, bloqueado o sin cajero → 422 con el
                  diálogo y el error (HX-Retarget #dialog)
    El límite de intentos (5 fallos, 15 minutos) lo aplica services.activate_device en la caché: borrar la cookie
    no lo reinicia.
    """
    next_url = _safe_next(request, reverse("pos:order_builder"))
    if request.user.is_authenticated:
        if request.method == "POST":
            return HttpResponse("Este dispositivo ya está activado.", status=409)
        return redirect(next_url)

    activate_url = reverse("accounts:activate_device")
    context = {"post_url": activate_url, "hx_target": "#dialog", "hx_swap": "innerHTML", "next_url": next_url,
               "error": ""}
    if request.method == "GET":
        if request.htmx:
            return render(request, "accounts/partials/activate_dialog.html", context)
        reopen_url = activate_url + "?" + urlencode({"next": next_url})  # «Escribir PIN» reopens the dialog
        return render(request, "accounts/activate_device.html", {**context, "activate_url": reopen_url})

    pin = "".join(request.POST.getlist("pin"))
    if not is_pin(pin):
        context["error"] = INCOMPLETE_PIN
        return _dialog_error(request, "accounts/partials/activate_dialog.html", context)
    try:
        cashier = services.activate_device(pin)
    except services.InvalidPinError as error:
        context["error"] = str(error)
    except services.NoCashierAvailableError:
        context["error"] = NO_CASHIER
    else:
        login(request, cashier)  # the session belongs to the cashier account, not to the Administrator
        return _done(request, next_url)
    return _dialog_error(request, "accounts/partials/activate_dialog.html", context)


@require_http_methods(["GET", "POST"])
@role_required()
def admin_pin(request):
    """
    CONTRATO VISTA–PLANTILLA — PIN de administrador (WBS 3.1.2, DEC-32)
    URL         : /accounts/pin/?module=<módulo>&next=<url> (accounts:admin_pin)
    Roles       : cualquier sesión activa (el dispositivo ya activado); sin sesión → activar el dispositivo
    Plantilla   : components/pin_dialog.html [fragmento, en #dialog]
    Contexto    : post_url, hx_target, hx_swap, module_label, next_url, error
    hx-target   : #dialog (innerHTML)
    Respuestas  : GET → 200 con el diálogo · POST con el PIN de un Administrador activo → abre el candado
                  30 minutos a su nombre (unlock_admin) y responde 204 + HX-Redirect a next · PIN incompleto,
                  incorrecto o bloqueado → 422 con el diálogo y el error (HX-Retarget #dialog)
    """
    module_label = request.GET.get("module", "")
    next_url = _safe_next(request, reverse("pos:order_builder"))
    if request.method == "GET":
        return render(request, "components/pin_dialog.html", pin_dialog_context(module_label, next_url))
    pin = "".join(request.POST.getlist("pin"))
    admin, error = (None, INCOMPLETE_PIN) if not is_pin(pin) else _pin_error(pin)
    if admin is None:
        return _dialog_error(request, "components/pin_dialog.html", pin_dialog_context(module_label, next_url, error))
    unlock_admin(request, admin)
    return _done(request, next_url)
