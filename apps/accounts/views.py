"""
Admin PIN dialog. Stand-in ONLY for the local integration branch (tarin/integracion-pantallas): the real view is
WBS 3.1.x (Yahir) and validates the PIN hash. Here any 6 digits unlock the modules (see apps/core/preview.py).
"""
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from apps.core import preview


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
