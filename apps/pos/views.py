"""
Views of M-PDV: Nueva venta (WBS 3.3.1–3.3.3, 3.3.5, 3.5.1, 3.5.7). Owner: Tarín (DEC-31); services: Jesús and Jared.

The dishes and modifiers come from the catalog, the order in progress lives in the Django session until it is
charged, the total is calcular_total over today's prices, and «Confirmar compra» calls services.confirm_sale, the
only write path of a sale. Opening and closing the till use services_cash_session behind the admin padlock: the
PIN dialog of apps/core/mixins.py identifies the Administrator (DEC-27, DEC-32), and unlocked_admin says who.
The views never compute money: Decimal amounts come from the catalog and the total from calcular_total.
sync_operations lives in views_sync.py (Jesús + Jared).
"""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Prefetch
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.catalog.models import Category, Dish
from apps.core import preview
from apps.core.mixins import admin_pin_required, is_admin_unlocked, role_required, unlocked_admin
from apps.inventory.services import check_min_stock
from apps.pos import services, services_cash_session as cash
from apps.pos.models import Modifier, ModifierKind, Sale
from apps.pos.services_pricing import calcular_total

ORDER_KEY = "pos_order"
PAYMENT_METHODS = [{"value": "efectivo", "label": "Efectivo", "icon": "banknote"},
                   {"value": "transferencia", "label": "Transferencia", "icon": "arrow-left-right"}]
CENT = Decimal("0.01")


def _url(name, *args):
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return "#"


def _cents(amount):
    return int((amount * 100).to_integral_value())


def _money(cents):
    return (Decimal(cents) / 100).quantize(CENT)


def _emoji(category):
    return category.emoji or category.name[:1].upper()


def _slug(category):
    return str(category.pk)


# --- Order in progress (Django session) ----------------------------------------------------------
# {"lines": [{"id": int, "dish_id": int, "quantity": int, "modifiers": [modifier pk, ...]}], "next_id": int,
#  "payment_method": "efectivo"|"transferencia"}. Lines with the same dish and modifiers are one line.

def _order(request):
    order = request.session.get(ORDER_KEY) or {}
    return {"lines": order.get("lines", []), "next_id": order.get("next_id", 1),
            "payment_method": order.get("payment_method", "efectivo")}


def _save(request, order):
    request.session[ORDER_KEY] = order


def _merge(order, dish_id, modifiers, quantity):
    """Adds quantity to the line with that dish and modifiers, or creates it. Returns the line."""
    modifiers = sorted(modifiers)
    for line in order["lines"]:
        if line["dish_id"] == dish_id and sorted(line["modifiers"]) == modifiers:
            line["quantity"] += quantity
            return line
    line = {"id": order["next_id"], "dish_id": dish_id, "quantity": quantity, "modifiers": modifiers}
    order["next_id"] += 1
    order["lines"].append(line)
    return line


def _decrease(order, line):
    line["quantity"] -= 1
    if line["quantity"] <= 0:
        order["lines"].remove(line)


def _priced(order):
    """
    The order with today's catalog: a line or modifier whose dish left the menu is dropped. Returns
    (lines, pedido): lines for the template and pedido with the shape of calcular_total and confirm_sale.
    """
    dishes = Dish.objects.filter(is_active=True).select_related("category").in_bulk(
        {line["dish_id"] for line in order["lines"]})
    definitions = Modifier.objects.select_related("ingredient").in_bulk(
        {pk for line in order["lines"] for pk in line["modifiers"]})
    lines, pedido = [], {"lineas": []}
    for line in order["lines"]:
        dish = dishes.get(line["dish_id"])
        if dish is None:
            continue
        mods = [definitions[pk] for pk in line["modifiers"]
                if pk in definitions and definitions[pk].dish_id == dish.pk]
        linea = {"platillo_id": dish.pk, "precio_base_centavos": _cents(dish.price), "cantidad": line["quantity"],
                 "modificadores": [{"tipo": "agregar" if m.kind == ModifierKind.ADD else "quitar",
                                    "insumo_id": m.ingredient_id,
                                    "ajuste_centavos": _cents(m.price_adjustment) if m.kind == ModifierKind.ADD else 0}
                                   for m in mods]}
        pedido["lineas"].append(linea)
        lines.append({"id": line["id"], "dish_id": dish.pk, "dish_name": dish.name, "emoji": _emoji(dish.category),
                      "modifiers": [_modifier_label(m) for m in mods], "quantity": line["quantity"],
                      "subtotal": _money(calcular_total({"lineas": [linea]})),
                      "remove_url": _url("pos:remove_item", line["id"]),
                      "edit_url": _url("pos:edit_line", line["id"]) if _has_modifiers(dish.pk) else ""})
    return lines, pedido


def _has_modifiers(dish_id):
    return Modifier.objects.filter(dish_id=dish_id).exists()


def _modifier_label(modifier):
    name = modifier.ingredient.name
    if modifier.kind == ModifierKind.REMOVE:
        return f"Sin {name.lower()}"
    if modifier.price_adjustment:
        return f"Extra {name.lower()} (+${modifier.price_adjustment:,.2f})"
    return f"Extra {name.lower()}"


def _order_context(order):
    lines, pedido = _priced(order)
    total = _money(calcular_total(pedido))
    count = sum(line["quantity"] for line in lines)
    return {"number": f"{Sale.objects.count() + 1:04d}", "status": "open", "item_count": count, "subtotal": total,
            "total": total, "payment_method": order["payment_method"] if lines else None, "lines": lines,
            "can_confirm": bool(lines)}, pedido


def _quantities(order):
    counts = {}
    for line in order["lines"]:
        counts[line["dish_id"]] = counts.get(line["dish_id"], 0) + line["quantity"]
    return counts


# --- Screen context -----------------------------------------------------------------------------

def _dish(dish, quantity=0):
    return {"id": dish.pk, "name": dish.name, "price": dish.price, "category": dish.category.name,
            "category_slug": _slug(dish.category), "emoji": _emoji(dish.category), "quantity": quantity,
            "add_url": _url("pos:add_item", dish.pk), "remove_url": _url("pos:remove_dish", dish.pk)}


def _dishes(order, category="todos", query=""):
    dishes = Dish.objects.filter(is_active=True).select_related("category").order_by("category__name", "name")
    if category not in ("", "todos"):
        dishes = dishes.filter(category_id=category) if category.isdigit() else dishes.none()
    if query:
        dishes = dishes.filter(name__icontains=query)
    counts = _quantities(order)
    return [_dish(d, counts.get(d.pk, 0)) for d in dishes]


def _categories(active="todos"):
    active = active or "todos"
    used = Category.objects.filter(dishes__is_active=True).distinct().order_by("name")
    chips = [{"slug": "todos", "name": "Todos"}] + [{"slug": _slug(c), "name": c.name} for c in used]
    return [{**c, "active": c["slug"] == active, "url": _url("pos:dish_list") + f"?category={c['slug']}"}
            for c in chips]


def _session_total(session):
    if session is None:
        return None
    totals = cash.sales_totals(session)
    return sum(totals.values(), Decimal("0.00"))


def _stock_notice():
    """«Alerta stock» when some ingredient is at or below its minimum (rule 3); it never blocks the sale."""
    low = check_min_stock().count()
    if not low:
        return None
    return {"detail": f"{low} insumo{'s' if low != 1 else ''} bajo{'s' if low != 1 else ''} · Ver inventario",
            "url": _url("inventory:ingredient_list")}


def _ticket_label(session, order):
    if session is None:
        return "Sin turno de caja abierto"
    return f"Ticket #{order['number']} · Turno del {session.business_date:%d/%m/%Y}"


def _top_bar(session):
    return {"cash_session_open": session is not None, "session_total": _session_total(session),
            "search_placeholder": "Buscar platillo por nombre (F2)...", "search_url": _url("pos:dish_list"),
            "search_target": "#dish-list"}


def _sale_context(request, category="todos", query=""):
    order = _order(request)
    order_ctx, _ = _order_context(order)
    return {"categories": _categories(category), "dishes": _dishes(order, category, query), "order": order_ctx,
            "payment_methods": PAYMENT_METHODS, "payment_url": _url("pos:set_payment_method"),
            "confirm_url": _url("pos:confirm_sale")}


def _screen_context(request):
    session = cash.current_session()
    context = {**_top_bar(session), **_sale_context(request)}
    context.update({"ticket_label": _ticket_label(session, context["order"]),
                    "stock_notice": _stock_notice() if session else None,
                    "open_session_url": _url("pos:open_session")})
    return context, session


def _dish_oob(request, dish_id):
    """The touched dish card, refreshed out of band so its counter matches the ticket."""
    dish = Dish.objects.filter(pk=dish_id, is_active=True).select_related("category").first()
    if dish is None:
        return None
    return _dish(dish, _quantities(_order(request)).get(dish.pk, 0))


def _alert(request, message, status):
    """Error without a field to show it on: an alert in #messages instead of replacing the target (HX-Retarget)."""
    response = render(request, "components/alert.html", {"message": message}, status=status)
    response["HX-Retarget"] = "#messages"
    response["HX-Reswap"] = "afterbegin"
    return response


def _retarget_dialog(response):
    """Errors keep the dialog open: the response replaces the content of #dialog instead of the original target."""
    response["HX-Retarget"] = "#dialog"
    response["HX-Reswap"] = "innerHTML"
    return response


def _summary(request, dish_id=None, **extra):
    context = {**_sale_context(request), "dish_oob": _dish_oob(request, dish_id) if dish_id else None, **extra}
    return render(request, "pos/partials/order_summary.html", context)


def _no_session(request):
    return _alert(request, cash.NoOpenSessionError().args[0], 409)


# --- Views --------------------------------------------------------------------------------------

@role_required()
@require_GET
def order_builder(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1, 3.5.1               Regla 12
    URL name    : pos:order_builder          Método: GET (carga completa o HTMX)
    Roles       : cashier, admin             (role_required)
    Plantilla   : pos/order_builder.html [página] · pos/partials/sale_area.html [fragmento, si request.htmx]
    HTMX        : hx-target="#sale-area" hx-swap="outerHTML"
    Contexto    :
        cash_session_open  bool    hay turno abierto (regla 12). False: se pinta «Caja cerrada»
        session_total      Decimal|None  lo cobrado en el turno, neto de cancelaciones (barra superior)
        ticket_label       str     «Ticket #0039 · Turno del 08/11/2026» (lo arma el servidor)
        stock_notice       dict|None  {detail: str, url: str}; None si ningún insumo está en su mínimo o debajo
        open_session_url   str     vista que devuelve el diálogo «Abrir caja»
        open_cash          dict|None  diálogo «Abrir caja» ya abierto: solo con la caja cerrada y el candado abierto
        categories         list    {slug, name, active: bool, url}; exactamente una activa; solo las que tienen
                                   platillos activos
        dishes             list    {id, name, price: Decimal, category, category_slug, emoji, quantity: int,
                                    add_url, remove_url}; quantity > 0: el platillo está en el ticket («En ticket»)
        order              dict    {number, status: "open", item_count: int, subtotal: Decimal, total: Decimal,
                                    payment_method: "efectivo"|"transferencia"|None, lines: list, can_confirm: bool}
        order.lines        list    {id, dish_id, dish_name, emoji, modifiers: list[str], quantity, subtotal: Decimal,
                                    remove_url, edit_url}; edit_url vacío si el platillo no tiene modificadores
        payment_methods    list    {value, label, icon}; payment_url, confirm_url  str
        + menú (procesador de contexto) y barra superior
    Controles (HATEOAS):
        order.can_confirm  -> «Confirmar compra» habilitado (pos:confirm_sale); si no, se ve deshabilitado
        not cash_session_open -> contenido deshabilitado y «Abrir caja» (pos:open_session)
    Errores     : 401/redirección sin sesión (dispositivo sin activar) · 403 sin rol
    """
    context, session = _screen_context(request)
    if session is None and not request.htmx and is_admin_unlocked(request):
        context["open_cash"] = _open_cash_dialog()
    template = "pos/partials/sale_area.html" if request.htmx else "pos/order_builder.html"
    return render(request, template, context)


@role_required()
@require_GET
def dish_list(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1
    URL name    : pos:dish_list              Método: GET (HTMX)
    Roles       : cashier, admin
    Plantilla   : pos/partials/dish_list.html [fragmento] + pos/partials/category_chips.html (hx-swap-oob)
    HTMX        : hx-target="#dish-list" hx-swap="outerHTML"; parámetros category (id o «todos») y q (búsqueda)
    Contexto    :
        categories  list  {slug, name, active: bool, url}
        dishes      list  igual que en pos:order_builder
        oob_chips   bool  True: el fragmento incluye los chips fuera de banda
    Sin HTMX redirige a pos:order_builder.
    """
    if not request.htmx:
        return HttpResponseRedirect(_url("pos:order_builder"))
    context = _sale_context(request, category=request.GET.get("category", "todos"),
                            query=request.GET.get("q", "").strip())
    context["oob_chips"] = True
    return render(request, "pos/partials/dish_list.html", context)


@role_required()
@require_POST
def add_item(request, dish_id):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1, 3.3.2
    URL name    : pos:add_item               Método: POST (HTMX)
    Roles       : cashier, admin
    Precondición: turno de caja abierto (regla 12)
    Plantilla   : pos/partials/order_summary.html [fragmento]
    HTMX        : hx-target="#order-summary" hx-swap="outerHTML"
    Contexto    : order, payment_methods (como en pos:order_builder); dish_oob: el platillo tocado, que se
                  devuelve fuera de banda (hx-swap-oob) para actualizar su contador
    Regla       : suma 1 a la línea del platillo sin modificadores (o la crea)
    Errores     : 409 sin turno abierto · 404 si el platillo no existe o no está activo (aviso en #messages)
    """
    if cash.current_session() is None:
        return _no_session(request)
    if not Dish.objects.filter(pk=dish_id, is_active=True).exists():
        return _alert(request, "Ese platillo ya no está en el menú.", 404)
    order = _order(request)
    _merge(order, dish_id, [], 1)
    _save(request, order)
    return _summary(request, dish_id)


@role_required()
@require_POST
def remove_item(request, line_id):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1
    URL name    : pos:remove_item            Método: POST (HTMX)
    Roles       : cashier, admin
    Plantilla   : pos/partials/order_summary.html [fragmento]
    HTMX        : hx-target="#order-summary" hx-swap="outerHTML"
    Contexto    : order, payment_methods; dish_oob del platillo de la línea
    Regla       : resta 1; al llegar a 0 la línea desaparece
    """
    order = _order(request)
    line = next((line for line in order["lines"] if line["id"] == line_id), None)
    if line is None:
        return _summary(request)
    _decrease(order, line)
    _save(request, order)
    return _summary(request, line["dish_id"])


@role_required()
@require_POST
def remove_dish(request, dish_id):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1
    URL name    : pos:remove_dish            Método: POST (HTMX), desde el Menú de cantidad
    Roles       : cashier, admin
    Plantilla   : pos/partials/order_summary.html [fragmento]
    HTMX        : hx-target="#order-summary" hx-swap="outerHTML"
    Contexto    : order, payment_methods; dish_oob como en pos:add_item
    Regla       : resta 1 a la última línea de ese platillo
    """
    order = _order(request)
    line = next((line for line in reversed(order["lines"]) if line["dish_id"] == dish_id), None)
    if line is not None:
        _decrease(order, line)
        _save(request, order)
    return _summary(request, dish_id)


@role_required()
@require_http_methods(["GET", "POST"])
def edit_line(request, line_id):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.3                      Regla 2
    URL name    : pos:edit_line              Método: GET (diálogo) · POST (guarda los modificadores de la línea)
    Roles       : cashier, admin
    Plantilla   : GET → pos/partials/line_modifiers.html [fragmento, diálogo en #dialog]
                  POST → pos/partials/order_summary.html [fragmento] + cierre del diálogo (close_dialog)
    HTMX        : el nombre de la línea del ticket hace hx-get con hx-target="#dialog";
                  el formulario hace hx-post con hx-target="#order-summary" hx-swap="outerHTML"
    Contexto    : line {id, dish_name, emoji, quantity}, post_url, hx_target, hx_swap,
                  options: list {value: pk, label, kind: "agregar"|"quitar", price: Decimal|None, checked: bool}
                  Envía modifier=<pk> por cada casilla marcada. Los modificadores aplican a todas las unidades de la
                  línea; si queda igual que otra línea del mismo platillo, se juntan.
    Regla       : quitar un ingrediente no cambia el precio; un extra suma su ajuste (lo calcula calcular_total)
    Errores     : 404 si la línea ya no está en el ticket
    """
    order = _order(request)
    line = next((line for line in order["lines"] if line["id"] == line_id), None)
    dish = Dish.objects.filter(pk=line["dish_id"]).select_related("category").first() if line else None
    if line is None or dish is None:
        return _alert(request, "Esa línea ya no está en el ticket.", 404)
    definitions = list(Modifier.objects.filter(dish=dish).select_related("ingredient")
                       .order_by("kind", "ingredient__name"))
    if request.method == "GET":
        options = [{"value": m.pk, "label": _modifier_label(m),
                    "kind": "agregar" if m.kind == ModifierKind.ADD else "quitar",
                    "price": m.price_adjustment if m.kind == ModifierKind.ADD else None,
                    "checked": m.pk in line["modifiers"]} for m in definitions]
        return render(request, "pos/partials/line_modifiers.html", {
            "line": {"id": line["id"], "dish_name": dish.name, "emoji": _emoji(dish.category),
                     "quantity": line["quantity"]},
            "options": options, "post_url": _url("pos:edit_line", line_id), "hx_target": "#order-summary",
            "hx_swap": "outerHTML"})
    allowed = {m.pk for m in definitions}
    chosen = sorted({int(pk) for pk in request.POST.getlist("modifier") if pk.isdigit() and int(pk) in allowed})
    order["lines"].remove(line)
    _merge(order, line["dish_id"], chosen, line["quantity"])
    _save(request, order)
    return _summary(request, close_dialog=True)


@role_required()
@require_POST
def set_payment_method(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.5                      Regla 4
    URL name    : pos:set_payment_method     Método: POST (HTMX); parámetro method = efectivo|transferencia
    Roles       : cashier, admin
    Plantilla   : pos/partials/order_summary.html [fragmento]
    HTMX        : hx-target="#order-summary" hx-swap="outerHTML"
    Contexto    : order (order.payment_method es el seleccionado), payment_methods
    Errores     : 422 si el método no es efectivo ni transferencia (regla 4): aviso en #messages (HX-Retarget)
    """
    method = request.POST.get("method", "")
    if method not in ("efectivo", "transferencia"):
        return _alert(request, "El método de pago solo puede ser efectivo o transferencia.", 422)
    order = _order(request)
    order["payment_method"] = method
    _save(request, order)
    return _summary(request)


@role_required()
@require_POST
def confirm_sale(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.5                      Reglas 1, 4, 7, 12 y 14
    URL name    : pos:confirm_sale           Método: POST (HTMX)
    Roles       : cashier, admin
    Precondición: turno de caja abierto (regla 12); order.can_confirm
    Plantilla   : pos/partials/order_summary.html [fragmento] con el ticket nuevo vacío
                  + session_total, stock_notice y la rejilla sin contadores fuera de banda (oob_after_sale)
    HTMX        : hx-target="#order-summary" hx-swap="outerHTML"
    Contexto    : order (vacío), payment_methods, session_total: Decimal, stock_notice, oob_after_sale: True,
                  dishes con quantity 0
    Regla       : el pedido se cobra con services.confirm_sale, en la misma transacción que descuenta el inventario;
                  lo cobrado es el total de calcular_total con los precios de hoy, a nombre de la cuenta del
                  dispositivo
    Errores     : 409 sin turno · 422 sin líneas, o si un platillo no tiene receta o ya no existe (aviso en
                  #messages; el ticket se conserva)
    """
    order = _order(request)
    order_ctx, pedido = _order_context(order)
    if not order_ctx["lines"]:
        return _alert(request, "Agrega al menos un platillo al ticket.", 422)
    try:
        services.confirm_sale(request.user, pedido, order["payment_method"], calcular_total(pedido))
    except cash.NoOpenSessionError as error:
        return _alert(request, str(error), 409)
    except services.SaleError as error:
        return _alert(request, str(error), 422)
    request.session.pop(ORDER_KEY, None)
    session = cash.current_session()
    context = {"oob_after_sale": True, "session_total": _session_total(session), "stock_notice": _stock_notice()}
    return render(request, "pos/partials/order_summary.html", {**_sale_context(request), **context})


def _open_cash_dialog(error=""):
    today = timezone.localdate()
    return {"shift_label": f"Turno del {today:%d/%m/%Y}", "opening_amount": None, "ask_pin": False,
            "post_url": _url("pos:open_session"), "hx_target": "#sale-area", "hx_swap": "outerHTML", "error": error}


def _decimal(value):
    return Decimal(str(value).replace("$", "").replace(",", "").strip())


@admin_pin_required("Caja")
@require_http_methods(["GET", "POST"])
def open_session(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.5.1                      Reglas 12 y 13; DEC-27, DEC-32
    URL name    : pos:open_session           Método: GET (diálogo) · POST (abre con services_cash_session.open_session)
    Roles       : admin: el candado del PIN (admin_pin_required) identifica al Administrador; con el candado
                  cerrado, el botón «Abrir caja» recibe primero el diálogo del PIN y, al escribirlo, la página vuelve
                  a Nueva venta con «Abrir caja» ya abierto
    Plantilla   : GET y 422 → pos/partials/open_cash_session.html [fragmento, diálogo en #dialog]
                  POST válido → pos/partials/sale_area.html [fragmento] + Estado de caja y total fuera de banda
    HTMX        : el diálogo hace hx-post con hx-target="#sale-area" hx-swap="outerHTML"
    Contexto    : shift_label: str, opening_amount: Decimal|None, ask_pin: False (en línea el PIN ya se pidió;
                  sin red lo pide static/pos/ con el verificador), error: str (si 422)
    Errores     : 422 con el diálogo y el error (fondo inicial inválido, ya hay un turno abierto o ya hubo uno
                  hoy), redirigido a #dialog con HX-Retarget para no reemplazar el área de venta
    """
    if request.method == "GET":
        return render(request, "pos/partials/open_cash_session.html", _open_cash_dialog())
    try:
        amount = _decimal(request.POST.get("opening_amount", ""))
        cash.open_session(unlocked_admin(request), amount)
    except InvalidOperation:
        return _retarget_dialog(render(request, "pos/partials/open_cash_session.html",
                                       _open_cash_dialog("Escribe el fondo inicial, por ejemplo 500.00."), status=422))
    except cash.CashSessionError as error:
        return _retarget_dialog(render(request, "pos/partials/open_cash_session.html",
                                       _open_cash_dialog(str(error)), status=422))
    preview.set_cash_open(request, True)  # until T18: the other screens still read the cash state from preview
    context, _ = _screen_context(request)
    context["oob_cash_status"] = True
    return render(request, "pos/partials/sale_area.html", context)


def _pending(request):
    """Operations the device has not synced: static/pos/ sends them in the X-Pendientes header (rule 5)."""
    value = request.headers.get("X-Pendientes", "0")
    return int(value) if value.isdigit() else 0


@admin_pin_required("Caja")
@require_http_methods(["GET", "POST"])
def close_session(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.5.7                      Reglas 5 y 13; DEC-27
    URL name    : pos:close_session          Método: GET (diálogo) · POST (cierra con
                                             services_cash_session.close_session)
    Roles       : admin (la página Caja ya pidió el PIN; DEC-32); queda a nombre de unlocked_admin
    Plantilla   : GET, 409 y 422 → pos/partials/cash_session_close.html [fragmento, diálogo en #dialog]
                  POST válido → sin cuerpo: HX-Redirect a pos:order_builder, que ya muestra «Caja cerrada», con el
                  resultado en un mensaje (django.contrib.messages)
    HTMX        : el botón «Cerrar caja» de Caja hace hx-get con hx-target="#dialog";
                  el formulario hace hx-post con hx-target="#dialog" hx-swap="innerHTML"
    Contexto    :
        shift_label       str      «Turno del 08/11/2026»
        expected_amount   Decimal  efectivo esperado: fondo inicial + ventas en efectivo, netas (expected_cash)
        pending_sync      int      operaciones sin sincronizar (encabezado X-Pendientes de static/pos/)
        closing_amount    str      lo que escribió el usuario (para no perderlo en un 422)
        post_url, hx_target, hx_swap   esta vista y el destino de los errores (#dialog)
        errors            dict     {closing_amount: mensaje}
        form_error        str      error general (409)
    Controles (HATEOAS):
        pending_sync > 0  -> aviso con cuántas faltan; el cierre se niega (regla 5)
    Errores     : 409 sin turno abierto o con operaciones sin sincronizar · 422 sin efectivo contado o con un monto
                  inválido. La diferencia de efectivo se registra y no bloquea (regla 13).
    """
    session = cash.current_session()
    pending = _pending(request)
    context = {"shift_label": f"Turno del {session.business_date:%d/%m/%Y}" if session else "",
               "expected_amount": cash.expected_cash(session) if session else Decimal("0.00"),
               "pending_sync": pending, "closing_amount": request.POST.get("closing_amount", ""),
               "post_url": _url("pos:close_session"), "hx_target": "#dialog", "hx_swap": "innerHTML", "errors": {},
               "form_error": ""}
    template = "pos/partials/cash_session_close.html"
    if session is None:
        context["form_error"] = cash.NoOpenSessionError().args[0]
        return _retarget_dialog(render(request, template, context, status=409))
    if request.method == "GET":
        return render(request, template, context)
    try:
        amount = _decimal(context["closing_amount"])
    except InvalidOperation:
        context["errors"]["closing_amount"] = "Escribe el efectivo contado, por ejemplo 3,620.00."
        return _retarget_dialog(render(request, template, context, status=422))
    try:
        closed = cash.close_session(unlocked_admin(request), amount, pending_sales=pending)
    except cash.PendingSalesError as error:
        context["form_error"] = str(error)
        return _retarget_dialog(render(request, template, context, status=409))
    except cash.InvalidAmountError as error:
        context["errors"]["closing_amount"] = str(error)
        return _retarget_dialog(render(request, template, context, status=422))
    except cash.CashSessionError as error:
        context["form_error"] = str(error)
        return _retarget_dialog(render(request, template, context, status=409))
    preview.set_cash_open(request, False)  # until T18
    difference = closed.cash_difference or Decimal("0.00")
    detail = "sin diferencia" if not difference else \
        f"diferencia de {'+' if difference > 0 else '−'}${abs(difference):,.2f}"
    messages.success(request, f"Caja cerrada, {detail}. El corte del turno quedó guardado.")
    response = HttpResponse(status=204)
    response["HX-Redirect"] = _url("pos:order_builder")
    return response
