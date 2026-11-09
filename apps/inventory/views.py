"""
Views of M-INV: Inventario (WBS 3.2.5, 3.2.7, 3.2.8; interface 2.2.3). Owner: Yahir (DEC-31); services: Diego.
Adapted from Yahir's Inventario screen (apps/core/templates/inventario.html) to base.html and the component library.

The data comes from the catalog's ingredients and inventory/services.py (register_purchase, register_waste,
is_low_stock). What is authorized with the PIN is recorded under that Administrator (unlocked_admin). «Agregar insumo»
is catalog:ingredient_create; the grid refreshes on its «ingredient-created» event, so inventory does not import the
catalog views. The cash state of the top bar still comes from apps/core/preview.py until T18 removes it.
"""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_GET, require_http_methods

from apps.catalog.models import Ingredient
from apps.core import preview
from apps.core.mixins import admin_pin_required, unlocked_admin
from apps.inventory import services


def _url(name, *args):
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return "#"


def _shell(request, search_placeholder=None, search_url="", search_target=""):
    """Top bar of the screen; the menu comes from apps.core.context_processors.shell."""
    return {"search_placeholder": search_placeholder, "hide_search": search_placeholder is None,
            "search_url": search_url, "search_target": search_target,
            "cash_session_open": preview.is_cash_open(request), "session_total": None}


# ------------------------------------------------------------------------------------------------ Inventario

def _quantity(value):
    """8.500 → 8.5 and 36.000 → 36, for labels."""
    value = value.normalize()
    return value.quantize(Decimal(1)) if value == value.to_integral() else value


def _level(ingredient):
    """Rule 3: alert when stock <= min_stock; critical with half the minimum or less (the server decides)."""
    if not services.is_low_stock(ingredient):
        return "normal"
    return "critico" if ingredient.stock <= ingredient.min_stock / 2 else "bajo"


def _card(ingredient):
    level = _level(ingredient)
    if ingredient.min_stock > 0:
        level_pct = int(max(6, min(100, ingredient.stock / ingredient.min_stock / 4 * 100)))  # bar: against 4× min
    else:
        level_pct = 100 if ingredient.stock > 0 else 6
    stock, min_stock, unit = _quantity(ingredient.stock), _quantity(ingredient.min_stock), ingredient.unit
    return {"id": ingredient.pk, "name": ingredient.name, "emoji": ingredient.name[:1].upper(), "stock": stock,
            "min_stock": min_stock, "unit": unit, "level": level, "level_pct": level_pct,
            "detail": f"Quedan {stock} {unit} de {min_stock} {unit} mínimos"}


def _ingredients(query=""):
    ingredients = Ingredient.objects.order_by("name")
    if query:
        ingredients = [i for i in ingredients if query.lower() in f"{i.name} {i.unit}".lower()]
    return [_card(ingredient) for ingredient in ingredients]


def _low_stock():
    rank = {"critico": 0, "bajo": 1}
    low = sorted((i for i in _ingredients() if i["level"] != "normal"), key=lambda i: (rank[i["level"]], i["name"]))
    return {"low_stock": low, "purchase_url": _url("inventory:register_purchase"),
            "waste_url": _url("inventory:register_waste")}


_require_pin = admin_pin_required("Inventario")


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
        ingredients        list   {id, name, emoji (inicial), stock, min_stock, unit, level, level_pct, detail}
        low_stock          list   los mismos, solo Bajo y Crítico (crítico primero)
        subtitle           str    «Existencias de insumos · N insumos»
        create_url, purchase_url, waste_url   diálogos en #dialog
    Controles   : «Agregar insumo» (Contorno, encabezado) · «Registrar compra» (Primario) · «Registrar merma»
                  (Secundario). Sin «Ordenar» ni «Filtros».
    """
    query = request.GET.get("q", "").strip()
    context = {"ingredients": _ingredients(query), "query": query, "create_url": _url("catalog:ingredient_create"),
               "list_url": _url("inventory:ingredient_list")}
    if request.htmx and not request.htmx.boosted:
        return render(request, "inventory/partials/ingredient_grid.html", context)
    context.update(_shell(request, "Buscar insumo por nombre o unidad (F2)...", _url("inventory:ingredient_list"),
                          "#ingredient-grid"))
    context.update(_low_stock())
    context["subtitle"] = f"Existencias de insumos · {Ingredient.objects.count()} insumos"
    return render(request, "inventory/ingredient_list.html", context)


_WASTE_REASONS = ["Caducidad", "Mal almacenamiento", "Daño en empaque", "Maduración", "Otro"]


def _ingredient_options():
    return [{"value": i.pk, "label": f"{i.name} ({i.unit})"} for i in Ingredient.objects.order_by("name")]


def _decimal(value):
    return Decimal(str(value).replace("$", "").replace(",", "").strip())


def _stock_form(request, kind):
    """Shared by register_purchase and register_waste: GET shows the dialog, POST validates and saves."""
    template = f"inventory/partials/{kind}_form.html"
    data = request.POST if request.method == "POST" else request.GET
    context = {"post_url": _url(f"inventory:register_{kind}"), "hx_target": "#messages", "hx_swap": "afterbegin",
               "ingredients": _ingredient_options(),
               "reasons": [{"value": r, "label": r} for r in _WASTE_REASONS],
               "values": {k: data.get(k, "") for k in ("ingredient", "quantity", "total_cost", "note", "reason",
                                                       "other_reason")},
               "errors": {}}
    if request.method == "GET":
        return render(request, template, context)
    v, e = context["values"], context["errors"]
    ingredient = Ingredient.objects.filter(pk=v["ingredient"]).first() if v["ingredient"].isdigit() else None
    if ingredient is None:
        e["ingredient"] = "Elige el insumo."
    quantity = total_cost = None
    try:
        quantity = _decimal(v["quantity"])
        if quantity <= 0:
            e["quantity"] = "La cantidad debe ser mayor que cero."
    except InvalidOperation:
        e["quantity"] = "Escribe la cantidad con números."
    if kind == "purchase":
        try:
            total_cost = _decimal(v["total_cost"])
            if total_cost <= 0:
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
    if not e:
        admin = unlocked_admin(request)
        try:
            if kind == "purchase":
                unit_cost = (total_cost / quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                services.register_purchase(ingredient, quantity, unit_cost, admin, note=v["note"].strip())
            else:
                note = v["other_reason"].strip() if v["reason"] == "Otro" else v["reason"]
                services.register_waste(ingredient, quantity, admin, note)
        except services.InvalidQuantityError as error:
            e["quantity"] = str(error)
    if e:
        response = render(request, template, context, status=422)
        response["HX-Retarget"], response["HX-Reswap"] = "#dialog", "innerHTML"
        return response
    message = (f"Compra de {ingredient.name} registrada." if kind == "purchase"
               else f"Merma de {ingredient.name} registrada.")
    return render(request, "inventory/partials/stock_saved.html",
                  {"message": message, "ingredients": _ingredients(), "list_url": _url("inventory:ingredient_list"),
                   **_low_stock()})


@_require_pin
@require_http_methods(["GET", "POST"])
def register_purchase(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    URL name  : inventory:register_purchase   GET (diálogo) · POST (registra)
    Roles     : admin (con PIN); la compra queda a nombre del Administrador que lo escribió
    Plantilla : GET y 422 → inventory/partials/purchase_form.html [#dialog]
                POST válido → inventory/partials/stock_saved.html: aviso en #messages, cierra #dialog y refresca
                «ingredient-grid» y «low-stock» fuera de banda
    Campos    : ingredient (select), quantity (en la unidad del insumo, > 0, hasta 3 decimales), total_cost (money,
                obligatorio; costo unitario = total / cantidad, nuevo costo del insumo), note
    """
    return _stock_form(request, "purchase")


@_require_pin
@require_http_methods(["GET", "POST"])
def register_waste(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    URL name  : inventory:register_waste   GET (diálogo) · POST (registra)
    Roles     : admin (con PIN); la merma queda a nombre del Administrador que lo escribió
    Plantilla : como register_purchase, con inventory/partials/waste_form.html
    Campos    : ingredient, quantity (> 0), reason (Caducidad, Mal almacenamiento, Daño en empaque, Maduración, Otro),
                other_reason (obligatorio con «Otro», máximo 50 caracteres). El motivo queda como nota de la merma.
    """
    return _stock_form(request, "waste")
