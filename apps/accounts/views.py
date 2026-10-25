"""
Admin PIN dialog. TEMPORARY stand-in (apps/core/preview.py, PR #44): any 6 digits unlock the modules. The real view
is WBS 3.1.x (Yahir) and validates the PIN hash with Diego's service.
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from apps.accounts import services
from apps.core import preview



MAX_PIN_ATTEMPTS = 5
PIN_LOCKOUT_SECONDS = 300

@require_http_methods(["GET", "POST"])
def admin_pin(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT (simulacro)
    URL name    : accounts:admin_pin         Método: GET (diálogo) · POST (valida)
    Plantilla   : components/pin_dialog.html [fragmento, en #dialog]
    Contexto    : module_label, next_url, post_url, hx_target, hx_swap, error
    Respuestas  : POST correcto → 204 con HX-Redirect a next · incorrecto → 422 con el diálogo (HX-Retarget #dialog)
    """
    module_label = request.GET.get("module", "")
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/pos/"
    if request.method == "GET":
        return render(request, "components/pin_dialog.html", preview.pin_dialog_context(module_label, next_url))
    pin = "".join(request.POST.getlist("pin"))
    if len(pin) != 6 or not pin.isdigit():
        response = render(request, "components/pin_dialog.html",
                          preview.pin_dialog_context(module_label, next_url, "Escribe los 6 dígitos del PIN."),
                          status=422)
        response["HX-Retarget"] = "#dialog"
        response["HX-Reswap"] = "innerHTML"
        return response
    preview.unlock(request)
    response = HttpResponse(status=204)
    response["HX-Redirect"] = next_url
    return response

@require_http_methods(["GET", "POST"])
def activate_device(request):
    activation_url = reverse("accounts:activate_device")
    sales_url = reverse("pos:order_builder")

    # Provisional: el estado se conserva en la sesión, no en un registro
    # permanente del dispositivo.
    if request.session.get("device_activated"):
        if request.method == "POST":
            return HttpResponse(status=409)
        return redirect(sales_url)

    error = None

    if request.method == "POST":
        now = timezone.now()
        locked_until = request.session.get("pin_locked_until")

        if locked_until and now.timestamp() < locked_until:
            error = "Demasiados intentos. Espera cinco minutos antes de volver a intentarlo."
        else:
            if locked_until:
                request.session.pop("pin_locked_until", None)
                request.session["pin_attempts"] = 0

            pin = "".join(request.POST.getlist("pin"))
            attempts = request.session.get("pin_attempts", 0)

            if len(pin) != 6 or not pin.isascii() or not pin.isdigit():
                error = "Escribe los 6 dígitos del PIN."
            else:
                try:
                    cashier = services.activate_device(pin)

                    # La sesión debe corresponder al cajero, no al administrador.
                    login(
                        request,
                        cashier,
                        backend=settings.AUTHENTICATION_BACKENDS[0],
                    )

                    request.session["device_activated"] = True
                    request.session["pin_attempts"] = 0
                    request.session.pop("pin_locked_until", None)

                    # Compatible con formularios HTMX y formularios normales.
                    if request.headers.get("HX-Request") == "true":
                        response = HttpResponse(status=204)
                        response["HX-Redirect"] = sales_url
                        return response

                    return redirect(sales_url)

                except services.InvalidPinError:
                    attempts += 1
                    request.session["pin_attempts"] = attempts

                    if attempts >= MAX_PIN_ATTEMPTS:
                        request.session["pin_locked_until"] = (
                            now + timedelta(seconds=PIN_LOCKOUT_SECONDS)
                        ).timestamp()
                        error = (
                            "Demasiados intentos fallidos. "
                            "Espera cinco minutos antes de volver a intentarlo."
                        )
                    else:
                        error = (
                            "El PIN no es válido. "
                            "Verifica los datos e inténtalo de nuevo."
                        )

                except services.NoCashierAvailableError:
                    error = (
                        "No hay una cuenta de cajero activa. "
                        "Contacta al administrador."
                    )

    dialog_context = preview.pin_dialog_context(
        module_label="Activar dispositivo",
        next_url=sales_url,
        error=error,
    )
    dialog_context["post_url"] = activation_url

    if request.headers.get("HX-Request") == "true":
        response = render(
            request,
            "components/pin_dialog.html",
            dialog_context,
            status=422 if error else 200,
        )
        if error:
            response["HX-Retarget"] = "#dialog"
            response["HX-Reswap"] = "innerHTML"
        return response

    pin_dialog = render_to_string(
        "components/pin_dialog.html",
        dialog_context,
        request=request,
    )

    return render(
        request,
        "accounts/activate_device.html",
        {
            "module_label": "Activar dispositivo",
            "pin_url": activation_url,
            "pin_dialog": pin_dialog,
        },
    )
