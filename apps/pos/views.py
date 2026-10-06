"""
Views of M-PDV: Nueva Venta (WBS 3.3.1, 3.3.5, 3.5.1). Owner: Tarín (DEC-31); services: Jared and Jesús.

CONTRACT DRAFT (phase 4): every view returns sample data with the exact shape of its context, so the
templates can be built and tested before the services exist. Replace the _sample_* helpers with service
calls without touching the templates. Pending, outside this file:
  - role and PIN checks with the mixin of apps/core/mixins.py (Jesús);
  - the shell context (menu, top bar) from a context processor in apps/core (Jesús);
  - modifiers (3.3.3) and the offline shell (3.4.4).
sync_operations lives in views_sync.py (Jesús + Jared).
"""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

# --- Sample data (contract draft) -------------------------------------------------------------
# Coherent with Figma rev. 1.1: 8 items, $480.00. Totals are literals: views never compute money.

_CATEGORIES = [
    {"slug": "todos", "name": "Todos"},
    {"slug": "burritos", "name": "Burritos"},
    {"slug": "desayunos", "name": "Desayunos"},
    {"slug": "guisados", "name": "Guisados"},
    {"slug": "bebidas", "name": "Bebidas"},
]

_DISHES = [
    {"id": 1, "name": "Burrito de asada", "price": Decimal("75.00"), "category": "Burritos", "category_slug": "burritos", "emoji": "🌯", "quantity": 2},
    {"id": 2, "name": "Burrito de pollo", "price": Decimal("75.00"), "category": "Burritos", "category_slug": "burritos", "emoji": "🌯", "quantity": 1},
    {"id": 3, "name": "Burrito de chicharrón", "price": Decimal("70.00"), "category": "Burritos", "category_slug": "burritos", "emoji": "🌯", "quantity": 0},
    {"id": 4, "name": "Frijol con queso", "price": Decimal("50.00"), "category": "Burritos", "category_slug": "burritos", "emoji": "🌯", "quantity": 1},
    {"id": 5, "name": "Chile relleno", "price": Decimal("80.00"), "category": "Burritos", "category_slug": "burritos", "emoji": "🌯", "quantity": 0},
    {"id": 6, "name": "Chilaquiles verdes", "price": Decimal("85.00"), "category": "Desayunos", "category_slug": "desayunos", "emoji": "🍳", "quantity": 1},
    {"id": 7, "name": "Machaca con huevo", "price": Decimal("70.00"), "category": "Desayunos", "category_slug": "desayunos", "emoji": "🍳", "quantity": 0},
    {"id": 8, "name": "Café de olla", "price": Decimal("25.00"), "category": "Bebidas", "category_slug": "bebidas", "emoji": "🥤", "quantity": 2},
    {"id": 9, "name": "Agua de horchata", "price": Decimal("30.00"), "category": "Bebidas", "category_slug": "bebidas", "emoji": "🥤", "quantity": 1},
]

_LINES = [
    {"id": 11, "dish_id": 1, "dish_name": "Burrito de asada", "emoji": "🌯", "modifiers": ["Sin cebolla", "Extra queso"], "quantity": 2, "subtotal": Decimal("170.00")},
    {"id": 12, "dish_id": 2, "dish_name": "Burrito de pollo", "emoji": "🌯", "modifiers": ["Con todo"], "quantity": 1, "subtotal": Decimal("75.00")},
    {"id": 13, "dish_id": 6, "dish_name": "Chilaquiles verdes", "emoji": "🍳", "modifiers": ["Con huevo (+$15)"], "quantity": 1, "subtotal": Decimal("100.00")},
    {"id": 14, "dish_id": 8, "dish_name": "Café de olla", "emoji": "🥤", "modifiers": ["Con piloncillo"], "quantity": 2, "subtotal": Decimal("50.00")},
    {"id": 15, "dish_id": 9, "dish_name": "Agua de horchata", "emoji": "🥤", "modifiers": ["Vaso de 1 L"], "quantity": 1, "subtotal": Decimal("30.00")},
    {"id": 16, "dish_id": 4, "dish_name": "Frijol con queso", "emoji": "🌯", "modifiers": ["Extra salsa"], "quantity": 1, "subtotal": Decimal("55.00")},
]

_MODULES = [
    ("pos", "Nueva Venta", "shopping-cart", False),
    ("products", "Productos", "package", True),
    ("inventory", "Inventario", "clipboard-list", True),
    ("cash", "Caja", "wallet", True),
    ("reports", "Reportes", "chart-column", True),
]


# URL names of the modules built so far; the others render «#» until they exist. reverse() by name is not an import,
# so pos does not depend on catalog (CLAUDE.md §7).
_MODULE_URLS = {"pos": "pos:order_builder", "products": "catalog:dish_catalog",
                "inventory": "inventory:ingredient_list", "cash": "reports:cash", "reports": "reports:reports"}


def _url(name, *args):
    """URL by name. The backend registers the routes in urls.py; until then the views render «#»."""
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return "#"


def _sample_order(payment_method="efectivo", empty=False):
    if empty:
        return {"id": 40, "number": "0040", "status": "open", "item_count": 0, "subtotal": Decimal("0.00"),
                "total": Decimal("0.00"), "payment_method": None, "lines": [], "can_confirm": False}
    return {"id": 39, "number": "0039", "status": "open", "item_count": 8, "subtotal": Decimal("480.00"),
            "total": Decimal("480.00"), "payment_method": payment_method, "lines": _LINES, "can_confirm": True}


def _sample_dishes(category="todos", query=""):
    dishes = [d for d in _DISHES if category in ("", "todos") or d["category_slug"] == category]
    if query:
        dishes = [d for d in dishes if query.lower() in d["name"].lower()]
    return dishes


def _shell_context(request, cash_open=True, session_total=Decimal("4850.00")):
    """Menu and top bar context. Temporary: will come from a context processor in apps/core (Jesús)."""
    return {
        "nav_modules": [{"key": k, "label": l, "icon": i, "url": _url(_MODULE_URLS[k]) if k in _MODULE_URLS else "#", "requires_pin": p}
                        for k, l, i, p in _MODULES],
        "active_module": "pos",
        "sync_pending": 0,
        "user_initials": "CM",
        "cash_session_open": cash_open,
        "session_total": session_total,
        "search_placeholder": "Buscar platillo por nombre, categoría o código (F2)...",
        "search_url": _url("pos:dish_list"),
        "search_target": "#dish-list",
    }


def _dish_oob(dish_id):
    """The touched dish card, refreshed out of band so its counter matches the ticket."""
    for dish in _DISHES:
        if dish["id"] == dish_id:
            return {**dish, "add_url": _url("pos:add_item", dish_id), "remove_url": _url("pos:remove_dish", dish_id)}
    return None


def _error(request, message, status):
    """Error without a field to show it on: an alert in #messages instead of replacing the target (HX-Retarget)."""
    response = render(request, "components/alert.html", {"message": message}, status=status)
    response["HX-Retarget"] = "#messages"
    response["HX-Reswap"] = "afterbegin"
    return response


def _sale_context(category="todos", query="", payment_method="efectivo"):
    order = _sample_order(payment_method)
    order["lines"] = [{**line, "remove_url": _url("pos:remove_item", line["id"])} for line in order["lines"]]
    return {
        "categories": [{**c, "active": c["slug"] == (category or "todos"),
                        "url": _url("pos:dish_list") + f"?category={c['slug']}"} for c in _CATEGORIES],
        "dishes": [{**d, "add_url": _url("pos:add_item", d["id"]), "remove_url": _url("pos:remove_dish", d["id"])}
                   for d in _sample_dishes(category, query)],
        "order": order,
        "payment_methods": [{"value": "efectivo", "label": "Efectivo", "icon": "banknote"},
                            {"value": "transferencia", "label": "Transferencia", "icon": "arrow-left-right"}],
        "payment_url": _url("pos:set_payment_method"),
        "confirm_url": _url("pos:confirm_sale"),
    }


# --- Views -------------------------------------------------------------------------------------

@require_GET
def order_builder(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1, 3.5.1               RF: pendiente 1.3.1
    URL name    : pos:order_builder          Método: GET (carga completa o HTMX)
    Roles       : cashier, admin             (mixin de apps/core/mixins.py, pendiente)
    Plantilla   : pos/order_builder.html [página] · pos/partials/sale_area.html [fragmento, si request.htmx]
    HTMX        : hx-target="#sale-area" hx-swap="outerHTML"
    Contexto    :
        cash_session_open  bool    hay turno abierto (regla 12). False: se pinta «Caja cerrada»
        ticket_label       str     «Ticket #0039 · Turno matutino · Para llevar» (lo arma el servidor)
        stock_notice       dict|None  {detail: str, url: str}; None si no hay insumos Bajo o Crítico
        open_session_url   str     vista que devuelve el diálogo «Abrir caja»
        categories         list    {slug, name, active: bool, url}; exactamente una activa
        dishes             list    {id, name, price: Decimal, category, category_slug, emoji, quantity: int,
                                    add_url, remove_url}; quantity > 0: el platillo está en el ticket («En ticket»)
        order              dict    {id, number, status: "open", item_count: int, subtotal: Decimal,
                                    total: Decimal, payment_method: "efectivo"|"transferencia"|None,
                                    lines: list, can_confirm: bool}
        order.lines        list    {id, dish_id, dish_name, emoji, modifiers: list[str], quantity, subtotal: Decimal,
                                    remove_url}
        payment_methods    list    {value, label, icon}; payment_url, confirm_url  str
        Las URL las arma la vista con reverse(); la plantilla nunca las construye.
        + contexto común del menú y la barra superior (base.html)
    Controles (HATEOAS):
        order.can_confirm  -> «Confirmar compra» habilitado (pos:confirm_sale); si no, se ve deshabilitado
        not cash_session_open -> contenido deshabilitado y «Abrir caja» (pos:open_session)
    Errores     : 403 sin rol
    Borrador    : ?estado=caja-cerrada muestra el estado sin turno; ?estado=ticket-vacio, el ticket vacío.
    """
    state = request.GET.get("estado", "")
    cash_open = state != "caja-cerrada"
    context = {
        **_shell_context(request, cash_open=cash_open, session_total=Decimal("4850.00") if cash_open else None),
        **_sale_context(),
        "cash_session_open": cash_open,
        "ticket_label": "Ticket #0039 · Turno matutino · Para llevar" if cash_open else "Sin turno de caja abierto",
        "stock_notice": {"detail": "3 insumos bajos · Ver inventario", "url": "#"} if cash_open else None,
        "open_session_url": _url("pos:open_session"),
    }
    if state == "ticket-vacio":
        context["order"] = _sample_order(empty=True)
        context["dishes"] = [{**d, "quantity": 0} for d in context["dishes"]]
    template = "pos/partials/sale_area.html" if request.htmx else "pos/order_builder.html"
    return render(request, template, context)


@require_GET
def dish_list(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1
    URL name    : pos:dish_list              Método: GET (HTMX)
    Roles       : cashier, admin
    Plantilla   : pos/partials/dish_list.html [fragmento] + pos/partials/category_chips.html (hx-swap-oob)
    HTMX        : hx-target="#dish-list" hx-swap="outerHTML"; parámetros category (slug) y q (búsqueda)
    Contexto    :
        categories  list  {slug, name, active: bool}
        dishes      list  igual que en pos:order_builder
        oob_chips   bool  True: el fragmento incluye los chips fuera de banda
    Sin HTMX redirige a pos:order_builder.
    """
    if not request.htmx:
        return HttpResponseRedirect(_url("pos:order_builder"))
    context = _sale_context(category=request.GET.get("category", "todos"), query=request.GET.get("q", "").strip())
    context["oob_chips"] = True
    return render(request, "pos/partials/dish_list.html", context)


@require_POST
def add_item(request, dish_id):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1
    URL name    : pos:add_item               Método: POST (HTMX)
    Roles       : cashier, admin
    Precondición: turno de caja abierto (regla 12)
    Plantilla   : pos/partials/order_summary.html [fragmento]
    HTMX        : hx-target="#order-summary" hx-swap="outerHTML"
    Contexto    : order, payment_methods (como en pos:order_builder); dish_oob: el platillo tocado, que se
                  devuelve fuera de banda (hx-swap-oob) para actualizar su contador
    Controles   : order.can_confirm -> «Confirmar compra»
    Errores     : 409 sin turno abierto (aviso en español en #messages)
    Borrador    : devuelve siempre el ticket de ejemplo; el servicio real suma 1 a la línea del platillo.
    """
    return render(request, "pos/partials/order_summary.html", {**_sale_context(), "dish_oob": _dish_oob(dish_id)})


@require_POST
def remove_item(request, line_id):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1
    URL name    : pos:remove_item            Método: POST (HTMX)
    Roles       : cashier, admin
    Plantilla   : pos/partials/order_summary.html [fragmento]
    HTMX        : hx-target="#order-summary" hx-swap="outerHTML"
    Contexto    : order, payment_methods
    Regla       : resta 1; al llegar a 0 la línea desaparece (lo decide el servicio); dish_oob del platillo de la línea
    """
    dish_id = next((line["dish_id"] for line in _LINES if line["id"] == line_id), None)
    return render(request, "pos/partials/order_summary.html", {**_sale_context(), "dish_oob": _dish_oob(dish_id)})


@require_POST
def remove_dish(request, dish_id):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1
    URL name    : pos:remove_dish            Método: POST (HTMX), desde el Menú de cantidad
    Roles       : cashier, admin
    Plantilla   : pos/partials/order_summary.html [fragmento]
    HTMX        : hx-target="#order-summary" hx-swap="outerHTML"
    Contexto    : order, payment_methods
    Regla       : resta 1 a la última línea de ese platillo (lo decide el servicio); dish_oob como en pos:add_item
    """
    return render(request, "pos/partials/order_summary.html", {**_sale_context(), "dish_oob": _dish_oob(dish_id)})


@require_POST
def set_payment_method(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.5
    URL name    : pos:set_payment_method     Método: POST (HTMX); parámetro method = efectivo|transferencia
    Roles       : cashier, admin
    Plantilla   : pos/partials/order_summary.html [fragmento]
    HTMX        : hx-target="#order-summary" hx-swap="outerHTML"
    Contexto    : order (order.payment_method es el seleccionado), payment_methods
    Errores     : 422 si el método no es efectivo ni transferencia (regla 4): aviso en #messages (HX-Retarget)
    """
    method = request.POST.get("method", "")
    if method not in ("efectivo", "transferencia"):
        return _error(request, "El método de pago solo puede ser efectivo o transferencia.", 422)
    return render(request, "pos/partials/order_summary.html", _sale_context(payment_method=method))


@require_POST
def confirm_sale(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.5
    URL name    : pos:confirm_sale           Método: POST (HTMX)
    Roles       : cashier, admin
    Precondición: turno de caja abierto (regla 12); order.can_confirm
    Plantilla   : pos/partials/order_summary.html [fragmento] con el ticket nuevo vacío
                  + session_total y stock_notice fuera de banda (hx-swap-oob)
    HTMX        : hx-target="#order-summary" hx-swap="outerHTML"
    Contexto    : order (vacío), payment_methods, session_total: Decimal, stock_notice, oob_after_sale: True,
                  y lo de pos:dish_list (dishes con quantity 0) para quitar los contadores
    Errores     : 409 sin turno · 422 sin método de pago o sin líneas (aviso en #messages)
    """
    context = {**_sale_context(), "order": _sample_order(empty=True), "oob_after_sale": True,
               "session_total": Decimal("5330.00"), "stock_notice": {"detail": "3 insumos bajos · Ver inventario", "url": "#"}}
    context["dishes"] = [{**d, "quantity": 0} for d in context["dishes"]]
    return render(request, "pos/partials/order_summary.html", context)


@require_http_methods(["GET", "POST"])
def open_session(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.5.1                      DEC-27, DEC-28
    URL name    : pos:open_session           Método: GET (diálogo) · POST (valida y abre)
    Roles       : admin (el PIN de 6 dígitos identifica al Administrador)
    Plantilla   : GET y 422 → pos/partials/open_cash_session.html [fragmento, diálogo en #dialog]
                  POST válido → pos/partials/sale_area.html [fragmento] + Estado de caja fuera de banda
    HTMX        : el diálogo hace hx-post con hx-target="#sale-area" hx-swap="outerHTML"
    Contexto    : shift_label: str, opening_amount: Decimal (sugerido), error: str (si 422)
    Errores     : 422 con el diálogo y el error («PIN incorrecto», «Escribe el fondo inicial»), redirigido a
                  #dialog con HX-Retarget para no reemplazar el área de venta
    Borrador    : acepta cualquier PIN de 6 dígitos; el servicio real valida el hash (DEC-28).
    """
    dialog = {"shift_label": "Turno matutino · 30/09/2026", "opening_amount": Decimal("500.00"),
              "post_url": _url("pos:open_session"), "hx_target": "#sale-area", "hx_swap": "outerHTML"}
    if request.method == "GET":
        return render(request, "pos/partials/open_cash_session.html", dialog)
    pin = "".join(request.POST.getlist("pin"))
    amount = request.POST.get("opening_amount", "").strip()
    error = ""
    if len(pin) != 6 or not pin.isdigit():
        error = "Escribe los 6 dígitos del PIN."
    elif not amount:
        error = "Escribe el fondo inicial."
    if error:
        response = render(request, "pos/partials/open_cash_session.html", {**dialog, "error": error}, status=422)
        response["HX-Retarget"] = "#dialog"
        response["HX-Reswap"] = "innerHTML"
        return response
    context = {**_shell_context(request), **_sale_context(), "cash_session_open": True, "oob_cash_status": True,
               "ticket_label": "Ticket #0039 · Turno matutino · Para llevar",
               "stock_notice": {"detail": "3 insumos bajos · Ver inventario", "url": "#"}}
    return render(request, "pos/partials/sale_area.html", context)


@require_http_methods(["GET", "POST"])
def close_session(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.5.7                      Reglas 5 y 13; DEC-27, DEC-30
    URL name    : pos:close_session          Método: GET (diálogo) · POST (cierra el turno)
    Roles       : admin (la página Caja ya pidió el PIN; DEC-32)
    Plantilla   : GET, 409 y 422 → pos/partials/cash_session_close.html [fragmento, diálogo en #dialog]
                  (plantilla de Yahir, pendiente; diseño en pantallas-y-fragmentos.md §10.6)
                  POST válido → sin cuerpo: HX-Redirect a pos:order_builder, que ya muestra «Caja cerrada», con el
                  resultado en un mensaje (django.contrib.messages)
    HTMX        : el botón «Cerrar caja» de reports/cash.html hace hx-get con hx-target="#dialog";
                  el formulario hace hx-post con hx-target="#dialog" hx-swap="innerHTML"
    Contexto    :
        shift_label       str      «Turno matutino · 30/09/2026» (lo arma el servidor)
        expected_amount   Decimal  efectivo esperado en caja (fondo inicial + ventas en efectivo; lo calcula el servicio)
        pending_sync      int      operaciones sin sincronizar; si es mayor que 0 el cierre se niega (regla 5)
        closing_amount    str      lo que escribió el usuario (para no perderlo en un 422)
        post_url          str      esta vista
        hx_target, hx_swap str     destino de los errores (#dialog)
        errors            dict     {closing_amount: mensaje}
        form_error        str      error general (409 por operaciones sin sincronizar)
    Controles (HATEOAS):
        pending_sync > 0  -> «Cerrar caja» deshabilitado y aviso con cuántas faltan
    Errores     : 409 con pending_sync > 0 («Faltan N operaciones por sincronizar») · 422 sin efectivo contado o
                  con un monto inválido. La diferencia de efectivo se registra y no bloquea (regla 13).
    Sin red     : el cierre se encola como cierre_turno (contrato v2, DEC-30); lo hace static/pos/ en la Fase 6.
    Borrador    : ?estado=pendientes simula 2 operaciones sin sincronizar.
    """
    pending = 2 if request.GET.get("estado") == "pendientes" or request.POST.get("estado") == "pendientes" else 0
    context = {"shift_label": "Turno matutino · 30/09/2026", "expected_amount": Decimal("3620.00"), "pending_sync": pending,
               "closing_amount": request.POST.get("closing_amount", ""), "post_url": _url("pos:close_session"),
               "hx_target": "#dialog", "hx_swap": "innerHTML", "errors": {}, "form_error": ""}
    template = "pos/partials/cash_session_close.html"
    if request.method == "GET":
        return render(request, template, context)
    if pending:
        context["form_error"] = f"Faltan {pending} operaciones por sincronizar. Sincroniza antes de cerrar la caja."
        return _retarget_dialog(render(request, template, context, status=409))
    try:
        if Decimal(context["closing_amount"].replace("$", "").replace(",", "")) < 0:
            context["errors"]["closing_amount"] = "El efectivo contado no puede ser negativo."
    except InvalidOperation:
        context["errors"]["closing_amount"] = "Escribe el efectivo contado, por ejemplo 3,620.00."
    if context["errors"]:
        return _retarget_dialog(render(request, template, context, status=422))
    # Borrador: el servicio real (close_session de services_cash_session.py) cierra el turno, genera el corte y
    # devuelve la diferencia de efectivo para el mensaje.
    messages.success(request, "Caja cerrada. El corte del turno se generó con las ventas sincronizadas.")
    response = HttpResponse(status=204)
    response["HX-Redirect"] = _url("pos:order_builder") + "?estado=caja-cerrada"
    return response


def _retarget_dialog(response):
    """Errors keep the dialog open: the response replaces the content of #dialog instead of the original target."""
    response["HX-Retarget"] = "#dialog"
    response["HX-Reswap"] = "innerHTML"
    return response
