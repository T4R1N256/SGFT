"""
Views of M-INV: Inventario (WBS 3.2.5, 3.2.7, 3.2.8; interface 2.2.3). Owner: Yahir (DEC-31); services: Diego.
Adapted from Yahir's Inventario screen (apps/core/templates/inventario.html) to base.html and the component library.

CONTRACT DRAFT: every view returns sample data with the exact shape of its context, so the templates can be built and
tested before the services exist (inventory/services.py: register_purchase, register_waste, check_min_stock).
«Agregar insumo» is catalog:ingredient_create; the grid refreshes on its «ingredient-created» event, so inventory does
not import catalog. Pending, outside this file:
  - role and PIN checks with the mixin of apps/core/mixins.py (Jesús);
  - the shell context (menu, top bar) from a context processor in apps/core (Jesús);
  - the routes in apps/inventory/urls.py (rutas-pendientes.md).
"""
from decimal import Decimal, InvalidOperation

from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_GET, require_http_methods

from apps.core import preview


def _url(name, *args):
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return "#"


def _shell(active, search_placeholder=None, search_url="", search_target=""):
    """Menu and top bar context. Temporary: will come from a context processor in apps/core (Jesús)."""
    modules = [("pos", "Nueva Venta", "shopping-cart", False, _url("pos:order_builder")),
               ("products", "Productos", "package", True, _url("catalog:dish_catalog")),
               ("inventory", "Inventario", "clipboard-list", True, _url("inventory:ingredient_list")),
               ("cash", "Caja", "wallet", True, _url("reports:cash")),
               ("reports", "Reportes", "chart-column", True, _url("reports:reports"))]
    return {"nav_modules": [{"key": k, "label": l, "icon": i, "requires_pin": p, "url": u} for k, l, i, p, u in modules],
            "active_module": active, "sync_pending": 0, "user_initials": "CM", "cash_session_open": True,
            "session_total": Decimal("4850.00"), "search_placeholder": search_placeholder,
            "hide_search": search_placeholder is None, "search_url": search_url, "search_target": search_target}


# ------------------------------------------------------------------------------------------------ Inventario

_INGREDIENTS = [  # name, emoji, stock, min_stock, unit
    ("Tortilla de harina", "🌮", Decimal("36"), Decimal("40"), "pzas"),
    ("Carne asada", "🥩", Decimal("8.5"), Decimal("3"), "kg"),
    ("Pollo deshebrado", "🍗", Decimal("1.2"), Decimal("3"), "kg"),
    ("Queso chihuahua", "🧀", Decimal("4.0"), Decimal("1.5"), "kg"),
    ("Frijol refrito", "🥣", Decimal("6.0"), Decimal("2"), "kg"),
    ("Huevo", "🥚", Decimal("28"), Decimal("30"), "pzas"),
    ("Café molido", "☕", Decimal("1.8"), Decimal("0.5"), "kg"),
    ("Chile poblano", "🌶️", Decimal("2.2"), Decimal("1"), "kg"),
]


def _ingredients(query=""):
    out = []
    for i, (name, emoji, stock, min_stock, unit) in enumerate(_INGREDIENTS, start=1):
        if query and query.lower() not in f"{name} {unit}".lower():
            continue
        ratio = stock / min_stock
        level = "critico" if ratio <= Decimal("0.5") else "bajo" if ratio <= 1 else "normal"
        # Rule 3: alert when stock <= min_stock. Critical: half the minimum or less (server decides).
        out.append({"id": i, "name": name, "emoji": emoji, "stock": stock.normalize() if unit == "pzas" else stock,
                    "min_stock": min_stock.normalize() if unit == "pzas" else min_stock, "unit": unit, "level": level,
                    "level_pct": int(max(6, min(100, ratio / 4 * 100)))})  # bar: stock against 4× the minimum
    return out


def _low_stock():
    rank = {"critico": 0, "bajo": 1}
    low = sorted((i for i in _ingredients() if i["level"] != "normal"), key=lambda i: rank[i["level"]])
    details = {"Pollo deshebrado": "Quedan 1.2 kg de 3 kg mínimos · alcanza para ~8 burritos",
               "Tortilla de harina": "Quedan 36 pzas de 40 mínimas", "Huevo": "Quedan 28 pzas de 30 mínimas"}
    for i in low:
        i["detail"] = details.get(i["name"], "")
    return {"low_stock": low, "purchase_suggestion": "Pollo 3 kg · Tortilla de harina 100 pzas · Huevo 1 caja (30 pzas)",
            "purchase_url": _url("inventory:register_purchase"), "waste_url": _url("inventory:register_waste")}


# Integration branch only: the whole screen asks for the admin PIN (apps/core/preview.py).
_require_pin = preview.require_admin_pin("Inventario", lambda request: preview.apply_to_shell(request, _shell("inventory")))


@_require_pin
@require_GET
def ingredient_list(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.5, 3.2.7, 3.2.8 · interfaz 2.2.3
    URL name    : inventory:ingredient_list      Método: GET
    Roles       : admin (con PIN; el desbloqueo dura 30 minutos)
    Plantilla   : request.htmx → inventory/partials/ingredient_grid.html [fragmento, id «ingredient-grid»]
                  si no → inventory/ingredient_list.html [página completa]
    HTMX        : el buscador de la barra hace hx-get con hx-target="#ingredient-grid"; la rejilla también se
                  refresca con hx-trigger="ingredient-created from:body" (catalog:ingredient_create)
    Contexto    :
        ingredients        list   {id, name, emoji, stock, min_stock, unit, level, level_pct} (nivel del servidor)
        low_stock          list   los mismos, solo Bajo y Crítico, con «detail»
        purchase_suggestion str   sugerencia de compra (servicio de Diego)
        subtitle           str    «Existencias de insumos · Última sincronización: … · 8 insumos» (sin red, la
                                  existencia es la copia local, DEC-29)
        create_url, purchase_url, waste_url   diálogos en #dialog
    Controles   : «Agregar insumo» (Contorno, encabezado) · «Registrar compra» (Primario) · «Registrar merma»
                  (Secundario). Sin «Ordenar» ni «Filtros».
    """
    query = request.GET.get("q", "").strip()
    ingredients = [] if request.GET.get("estado") == "vacio" else _ingredients(query)
    context = {"ingredients": ingredients, "query": query, "create_url": _url("catalog:ingredient_create"),
               "list_url": _url("inventory:ingredient_list")}
    if request.htmx and not request.htmx.boosted:
        return render(request, "inventory/partials/ingredient_grid.html", context)
    context.update(preview.apply_to_shell(request, _shell("inventory", "Buscar insumo por nombre o unidad (F2)...", _url("inventory:ingredient_list"),
                          "#ingredient-grid")))
    context.update(_low_stock())
    context["subtitle"] = f"Existencias de insumos · Última sincronización: hoy, 10:45 AM · {len(_INGREDIENTS)} insumos"
    return render(request, "inventory/ingredient_list.html", context)


_WASTE_REASONS = ["Caducidad", "Mal almacenamiento", "Daño en empaque", "Maduración", "Otro"]


def _ingredient_options():
    return [{"value": i["id"], "label": f"{i['emoji']} {i['name']} ({i['unit']})"} for i in _ingredients()]


def _decimal(value):
    return Decimal(str(value).replace("$", "").replace(",", "").strip())


def _stock_form(request, kind):
    """Shared by register_purchase and register_waste: GET shows the dialog, POST validates and refreshes."""
    template = f"inventory/partials/{kind}_form.html"
    data = request.POST if request.method == "POST" else request.GET
    context = {"post_url": _url(f"inventory:register_{kind}"), "hx_target": "#messages", "hx_swap": "afterbegin",
               "ingredients": _ingredient_options(),
               "reasons": [{"value": r, "label": r} for r in _WASTE_REASONS],
               "values": {k: data.get(k, "") for k in ("ingredient", "quantity", "total_cost", "note", "reason", "other_reason")},
               "errors": {}}
    if request.method == "GET":
        return render(request, template, context)
    v, e = context["values"], context["errors"]
    if not v["ingredient"]:
        e["ingredient"] = "Elige el insumo."
    try:
        if _decimal(v["quantity"]) <= 0:
            e["quantity"] = "La cantidad debe ser mayor que cero."
    except InvalidOperation:
        e["quantity"] = "Escribe la cantidad con números."
    if kind == "purchase":
        try:
            if _decimal(v["total_cost"]) <= 0:
                e["total_cost"] = "El costo total debe ser mayor que cero."
        except InvalidOperation:
            e["total_cost"] = "Escribe el costo total de la compra."
    else:
        if v["reason"] not in _WASTE_REASONS:
            e["reason"] = "Elige el motivo."
        elif v["reason"] == "Otro" and not v["other_reason"].strip():
            e["other_reason"] = "Especifica el motivo."
        elif len(v["other_reason"]) > 50:
            e["other_reason"] = "Máximo 50 caracteres."
    if e:
        response = render(request, template, context, status=422)
        response["HX-Retarget"], response["HX-Reswap"] = "#dialog", "innerHTML"
        return response
    name = next(i["name"] for i in _ingredients() if str(i["id"]) == v["ingredient"])
    message = f"Compra de {name} registrada." if kind == "purchase" else f"Merma de {name} registrada."
    response = render(request, "inventory/partials/stock_saved.html",
                      {"message": message, "ingredients": _ingredients(), "list_url": _url("inventory:ingredient_list"),
                       **_low_stock()})
    return response


@_require_pin
@require_http_methods(["GET", "POST"])
def register_purchase(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    URL name  : inventory:register_purchase   GET (diálogo) · POST (registra)
    Plantilla : GET y 422 → inventory/partials/purchase_form.html [#dialog]
                POST válido → inventory/partials/stock_saved.html: aviso en #messages, cierra #dialog y refresca
                «ingredient-grid» y «low-stock» fuera de banda
    Campos    : ingredient (select), quantity (en la unidad del insumo, > 0), total_cost (money, obligatorio), note
    """
    return _stock_form(request, "purchase")


@_require_pin
@require_http_methods(["GET", "POST"])
def register_waste(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    URL name  : inventory:register_waste   GET (diálogo) · POST (registra)
    Plantilla : como register_purchase, con inventory/partials/waste_form.html
    Campos    : ingredient, quantity (> 0), reason (Caducidad, Mal almacenamiento, Daño en empaque, Maduración, Otro),
                other_reason (obligatorio con «Otro», máximo 50 caracteres)
    """
    return _stock_form(request, "waste")
