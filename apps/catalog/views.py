"""
Views of the Productos screen (WBS 3.2.1, 3.2.3; DEC-25). Owner: Tarín (DEC-31); services: Diego.

CONTRACT DRAFT (phase 4): every view returns sample data with the exact shape of its context, so the
templates can be built and tested before the services exist. Replace the _sample_* helpers with calls to
apps/catalog/services.py without touching the templates. Pending, outside this file:
  - admin role and PIN check with the mixin of apps/core/mixins.py (Jesús): the whole screen is admin-only;
  - the shell context (menu, top bar) from a context processor in apps/core (Jesús);
  - the routes in urls.py and the catalog include in config/urls.py (rutas-pendientes.md).
catalog depends on no other app (CLAUDE.md §7), so it does not import from pos.
"""
from decimal import Decimal, InvalidOperation

from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_GET, require_http_methods

# --- Sample data (contract draft) -------------------------------------------------------------
# Coherent with Figma 03 · Productos (rev. 1.1). The emoji comes from the category (DEC-30).

_CATEGORIES = [
    {"value": "burritos", "label": "Burritos", "emoji": "🌯"},
    {"value": "desayunos", "label": "Desayunos", "emoji": "🍳"},
    {"value": "guisados", "label": "Guisados", "emoji": "🍲"},
    {"value": "bebidas", "label": "Bebidas", "emoji": "🥤"},
]

_DISHES = [
    (1, "Burrito de asada", "Tortilla de harina, carne asada, frijol, queso y salsa de la casa.", "75.00", "burritos", "disponible"),
    (2, "Burrito de pollo", "Pollo deshebrado en salsa roja, frijol y queso chihuahua.", "75.00", "burritos", "disponible"),
    (3, "Burrito de chicharrón", "Chicharrón prensado en salsa verde con frijol refrito.", "70.00", "burritos", "disponible"),
    (4, "Frijol con queso", "Frijol refrito con queso chihuahua gratinado.", "50.00", "burritos", "disponible"),
    (5, "Chile relleno", "Chile poblano relleno de queso, capeado, en tortilla de harina.", "80.00", "burritos", "pocas"),
    (6, "Chilaquiles verdes", "Totopos en salsa verde con crema, queso fresco y cebolla.", "85.00", "desayunos", "disponible"),
    (7, "Machaca con huevo", "Machaca de res con huevo, tomate y chile verde.", "70.00", "desayunos", "disponible"),
    (8, "Asado de puerco", "Porción de 250 g con arroz y frijoles de la olla.", "65.00", "guisados", "disponible"),
    (9, "Café de olla", "Café con canela y piloncillo, vaso de 12 oz.", "25.00", "bebidas", "disponible"),
]

_INGREDIENTS = [
    {"value": 1, "label": "Tortilla de harina", "unit": "pzas"},
    {"value": 2, "label": "Carne asada", "unit": "kg"},
    {"value": 3, "label": "Pollo deshebrado", "unit": "kg"},
    {"value": 4, "label": "Queso chihuahua", "unit": "kg"},
    {"value": 5, "label": "Frijol refrito", "unit": "kg"},
    {"value": 6, "label": "Huevo", "unit": "pzas"},
    {"value": 7, "label": "Café molido", "unit": "kg"},
    {"value": 8, "label": "Chile poblano", "unit": "kg"},
]

_RECIPE = [(1, "1"), (2, "0.15"), (5, "0.05"), (4, "0.03")]  # Burrito de asada


def _url(name, *args):
    """URL by name. The backend registers the routes in urls.py; until then the views render «#»."""
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return "#"


def _category(slug):
    return next(c for c in _CATEGORIES if c["value"] == slug)


def _dish(row):
    dish_id, name, description, price, slug, availability = row
    category = _category(slug)
    return {
        "id": dish_id, "name": name, "description": description, "price": Decimal(price),
        "category": category["label"], "category_value": slug, "emoji": category["emoji"],
        "availability": availability, "active": True,
        "edit_url": _url("catalog:dish_edit", dish_id), "recipe_url": _url("catalog:recipe_edit", dish_id),
    }


def _sample_dishes(query=""):
    dishes = [_dish(row) for row in _DISHES]
    if query:
        dishes = [d for d in dishes if query.lower() in d["name"].lower()]
    return dishes


def _sample_dish(dish_id):
    return next((_dish(row) for row in _DISHES if row[0] == dish_id), None)


def _recipe_line(index, ingredient_id="", quantity="", error=""):
    ingredient = next((i for i in _INGREDIENTS if str(i["value"]) == str(ingredient_id)), None)
    return {"index": index, "ingredient": ingredient_id, "quantity": quantity,
            "unit": ingredient["unit"] if ingredient else "", "error": error}


def _shell_context(search_url):
    """Menu and top bar context. Temporary: will come from a context processor in apps/core (Jesús)."""
    modules = [("pos", "Nueva Venta", "shopping-cart", False, _url("pos:order_builder")),
               ("products", "Productos", "package", True, _url("catalog:dish_catalog")),
               ("inventory", "Inventario", "clipboard-list", True, "#"),
               ("cash", "Caja", "wallet", True, "#"),
               ("reports", "Reportes", "chart-column", True, "#")]
    return {
        "nav_modules": [{"key": k, "label": l, "icon": i, "requires_pin": p, "url": u} for k, l, i, p, u in modules],
        "active_module": "products",
        "sync_pending": 0,
        "user_initials": "CM",
        "cash_session_open": True,
        "session_total": Decimal("4850.00"),
        "search_placeholder": "Buscar platillo en el catálogo (F2)...",
        "search_url": search_url,
        "search_target": "#dish-grid",
    }


def _grid_context(query=""):
    dishes = _sample_dishes(query)
    return {"dishes": dishes, "active_count": sum(1 for d in dishes if d["active"]),
            "create_url": _url("catalog:dish_create")}


def _dialog_error(request, template, context):
    """422 with the same dialog and its errors, retargeted to #dialog so it does not replace the grid."""
    response = render(request, template, context, status=422)
    response["HX-Retarget"] = "#dialog"
    response["HX-Reswap"] = "innerHTML"
    return response


def _dish_form_context(dish=None, data=None, errors=None):
    data = data or {}
    return {
        "dish": dish,
        "post_url": _url("catalog:dish_edit", dish["id"]) if dish else _url("catalog:dish_create"),
        "hx_target": f"#catalog-dish-{dish['id']}" if dish else "#dish-grid",
        "hx_swap": "outerHTML",
        "categories": _CATEGORIES,
        "values": {
            "name": data.get("name", dish["name"] if dish else ""),
            "category": data.get("category", dish["category_value"] if dish else ""),
            "price": data.get("price", dish["price"] if dish else None),
            "description": data.get("description", dish["description"] if dish else ""),
            "active": data.get("active", "on") if data else (dish["active"] if dish else True),
        },
        "errors": errors or {},
    }


def _validate_dish(data):
    """Draft: only checks the shape the form needs. The service (Diego) owns the real rules."""
    errors = {}
    if not data.get("name", "").strip():
        errors["name"] = "Escribe el nombre del platillo."
    if data.get("category") not in [c["value"] for c in _CATEGORIES]:
        errors["category"] = "Elige una categoría."
    try:
        if Decimal(data.get("price", "").replace("$", "").replace(",", "")) <= 0:
            errors["price"] = "El precio debe ser mayor que cero."
    except InvalidOperation:
        errors["price"] = "Escribe el precio con números, por ejemplo 75.00."
    if len(data.get("description", "")) > 120:
        errors["description"] = "La descripción admite 120 caracteres como máximo."
    return errors


# --- Views -------------------------------------------------------------------------------------

@require_GET
def dish_catalog(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.1                      DEC-25
    URL name    : catalog:dish_catalog       Método: GET (carga completa o HTMX); parámetro q (búsqueda)
    Roles       : admin, con PIN de Administrador (mixin de apps/core/mixins.py, pendiente)
    Plantilla   : catalog/products.html [página] · catalog/partials/dish_grid.html [fragmento, si request.htmx]
    HTMX        : el buscador hace hx-get con hx-target="#dish-grid" hx-swap="outerHTML"
    Contexto    :
        dishes        list  {id, name, description, price: Decimal, category, category_value, emoji,
                             availability: "disponible"|"pocas"|"agotado", active: bool, edit_url, recipe_url}
                            availability la decide el servidor con las existencias de la receta
        active_count  int   platillos activos (subtítulo)
        create_url    str   diálogo «Agregar platillo» (botón a la derecha del encabezado)
        + contexto común del menú y la barra superior (base.html)
    Controles (HATEOAS):
        edit_url / recipe_url / create_url presentes -> «Editar», «Receta», botón «Agregar platillo»
    Errores     : 403 sin rol o sin PIN
    """
    query = request.GET.get("q", "").strip()
    context = {**_shell_context(_url("catalog:dish_catalog")), **_grid_context(query)}
    template = "catalog/partials/dish_grid.html" if request.htmx else "catalog/products.html"
    return render(request, template, context)


@require_http_methods(["GET", "POST"])
def dish_create(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.1
    URL name    : catalog:dish_create        Método: GET (diálogo) · POST (guarda)
    Roles       : admin
    Plantilla   : GET y 422 → catalog/partials/dish_form.html [fragmento, diálogo en #dialog]
                  POST válido → catalog/partials/dish_grid.html [fragmento] + cierre del diálogo (hx-swap-oob)
    HTMX        : el formulario hace hx-post con hx-target="#dish-grid" hx-swap="outerHTML"
    Contexto    : dish: None, post_url, hx_target, hx_swap, categories: list {value, label, emoji},
                  values: {name, category, price, description, active}, errors: {campo: mensaje}
                  La receta se edita aparte, con catalog:recipe_edit (botón «Receta» de cada tarjeta).
    Errores     : 422 con el diálogo y el error bajo cada campo (HX-Retarget="#dialog")
    Borrador    : al guardar devuelve la rejilla de ejemplo; el servicio real crea el platillo.
    """
    if request.method == "GET":
        return render(request, "catalog/partials/dish_form.html", _dish_form_context())
    errors = _validate_dish(request.POST)
    if errors:
        return _dialog_error(request, "catalog/partials/dish_form.html", _dish_form_context(data=request.POST, errors=errors))
    return render(request, "catalog/partials/dish_grid.html", {**_grid_context(), "close_dialog": True})


@require_http_methods(["GET", "POST"])
def dish_edit(request, dish_id):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.1
    URL name    : catalog:dish_edit          Método: GET (diálogo) · POST (guarda)
    Roles       : admin
    Plantilla   : GET y 422 → catalog/partials/dish_form.html [fragmento, diálogo en #dialog]
                  POST válido → catalog/partials/dish_card.html [fragmento] + cierre del diálogo (hx-swap-oob)
    HTMX        : el formulario hace hx-post con hx-target="#catalog-dish-<id>" hx-swap="outerHTML"
    Contexto    : como catalog:dish_create, con dish (el platillo) y values prellenados; tras guardar, dish
    Errores     : 404 si el platillo no existe · 422 como en catalog:dish_create
    """
    dish = _sample_dish(dish_id)
    if dish is None:
        return render(request, "components/alert.html", {"message": "Ese platillo no existe."}, status=404)
    if request.method == "GET":
        return render(request, "catalog/partials/dish_form.html", _dish_form_context(dish))
    errors = _validate_dish(request.POST)
    if errors:
        return _dialog_error(request, "catalog/partials/dish_form.html", _dish_form_context(dish, request.POST, errors))
    saved = {**dish, "name": request.POST["name"].strip(), "description": request.POST.get("description", "").strip(),
             "price": Decimal(request.POST["price"].replace("$", "").replace(",", "")), "active": "active" in request.POST}
    return render(request, "catalog/partials/dish_card.html", {"dish": saved, "close_dialog": True})


@require_http_methods(["GET", "POST"])
def recipe_edit(request, dish_id):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.3                      DEC-25 (también se abre desde Inventario)
    URL name    : catalog:recipe_edit        Método: GET (diálogo) · POST (guarda la receta completa)
    Roles       : admin
    Plantilla   : GET y 422 → catalog/partials/recipe_form.html [fragmento, diálogo en #dialog]
                  POST válido → solo cierra el diálogo (hx-swap-oob) y muestra un aviso en #messages
    HTMX        : hx-post con hx-target="#messages" hx-swap="afterbegin"
    Contexto    : dish, post_url, hx_target, hx_swap, add_line_url, ingredients: list {value, label, unit},
                  lines: list {index, ingredient, quantity, unit, error}, next_index: int, form_error: str
                  Cada fila envía ingredient_<n> y quantity_<n>; la unidad la decide el insumo (no se edita).
    Errores     : 422 con el diálogo: insumo repetido, cantidad no positiva o receta vacía
    """
    dish = _sample_dish(dish_id)
    if dish is None:
        return render(request, "components/alert.html", {"message": "Ese platillo no existe."}, status=404)
    base = {"dish": dish, "post_url": _url("catalog:recipe_edit", dish_id), "add_line_url": _url("catalog:add_recipe_line"),
            "ingredients": _INGREDIENTS, "hx_target": "#messages", "hx_swap": "afterbegin"}
    if request.method == "GET":
        lines = [_recipe_line(i, ing, qty) for i, (ing, qty) in enumerate(_RECIPE)]
        return render(request, "catalog/partials/recipe_form.html", {**base, "lines": lines, "next_index": len(lines)})
    indexes = sorted({int(k.split("_")[1]) for k in request.POST if k.startswith("ingredient_")})
    lines, seen, has_error = [], set(), False
    for i in indexes:
        ingredient, quantity = request.POST.get(f"ingredient_{i}", ""), request.POST.get(f"quantity_{i}", "").strip()
        error = ""
        try:
            if not ingredient:
                error = "Elige un insumo."
            elif ingredient in seen:
                error = "Ese insumo ya está en la receta."
            elif Decimal(quantity) <= 0:
                error = "La cantidad debe ser mayor que cero."
        except InvalidOperation:
            error = "Escribe la cantidad con números."
        seen.add(ingredient)
        has_error = has_error or bool(error)
        lines.append(_recipe_line(i, ingredient, quantity, error))
    if not lines or has_error:
        form_error = "" if lines else "Agrega al menos un insumo a la receta."
        return _dialog_error(request, "catalog/partials/recipe_form.html",
                             {**base, "lines": lines, "next_index": (indexes[-1] + 1) if indexes else 0, "form_error": form_error})
    return render(request, "catalog/partials/recipe_saved.html", {"dish": dish})


@require_GET
def add_recipe_line(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.3
    URL name    : catalog:add_recipe_line    Método: GET (HTMX); parámetro index
    Roles       : admin
    Plantilla   : catalog/partials/recipe_line.html [fragmento] — una fila vacía, más fuera de banda el botón
                  «Agregar insumo» con el índice siguiente y la eliminación del aviso de receta vacía
    HTMX        : «Agregar insumo» hace hx-get con hx-target="#recipe-lines" hx-swap="beforeend"
    Contexto    : line: {index, ingredient: "", quantity: "", unit: "", error: ""}, ingredients,
                  add_line_url, next_index: int, oob: True
    """
    try:
        index = int(request.GET.get("index", "0"))
    except ValueError:
        index = 0
    return render(request, "catalog/partials/recipe_line.html",
                  {"line": _recipe_line(index), "ingredients": _INGREDIENTS, "add_line_url": _url("catalog:add_recipe_line"),
                   "next_index": index + 1, "oob": True})


_UNITS = [{"value": u, "label": u} for u in ("kg", "g", "L", "ml", "pzas")]  # agreed list (DEC-30); the server owns it


def _ingredient_form_context(data=None, errors=None, form_error=""):
    data = data or {}
    return {"post_url": _url("catalog:ingredient_create"), "hx_target": "#messages", "hx_swap": "afterbegin",
            "units": _UNITS, "values": {k: data.get(k, "") for k in ("name", "unit", "initial_stock", "initial_cost", "min_stock")},
            "errors": errors or {}, "form_error": form_error}


def _decimal(value):
    return Decimal(str(value).replace("$", "").replace(",", "").strip())


@require_http_methods(["GET", "POST"])
def ingredient_create(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.2                      DEC-30 (costo por compra), regla 3 (mínimo)
    URL name    : catalog:ingredient_create  Método: GET (diálogo) · POST (da de alta el insumo)
    Roles       : admin (Inventario ya pidió el PIN; DEC-32)
    Plantilla   : GET y 422 → catalog/partials/ingredient_form.html [fragmento, diálogo en #dialog]
                  POST válido → catalog/partials/ingredient_saved.html [fragmento]: aviso en #messages y cierre del
                  diálogo (hx-swap-oob), más el evento HX-Trigger «ingredient-created» para que Inventario (Yahir)
                  refresque su rejilla sin que catalog dependa de inventory.
    HTMX        : el tile «Agregar insumo» de Inventario hace hx-get con hx-target="#dialog";
                  el formulario hace hx-post con hx-target="#messages" hx-swap="afterbegin"
    Contexto    : post_url, hx_target, hx_swap, units: list {value, label},
                  values: {name, unit, initial_stock, initial_cost, min_stock}, errors: {campo: mensaje}
    Reglas      : la unidad se fija al dar de alta el insumo (compras, mermas y recetas la toman de ahí); la existencia
                  inicial se registra como compra inicial y, si es mayor que 0, exige su costo total (DEC-30).
    Errores     : 422 con el diálogo y el error bajo cada campo (HX-Retarget="#dialog")
    """
    if request.method == "GET":
        return render(request, "catalog/partials/ingredient_form.html", _ingredient_form_context())
    data, errors = request.POST, {}
    if not data.get("name", "").strip():
        errors["name"] = "Escribe el nombre del insumo."
    if data.get("unit") not in [u["value"] for u in _UNITS]:
        errors["unit"] = "Elige la unidad de medida."
    stock = Decimal("0")
    try:
        stock = _decimal(data.get("initial_stock") or "0")
        if stock < 0:
            errors["initial_stock"] = "La existencia no puede ser negativa."
    except InvalidOperation:
        errors["initial_stock"] = "Escribe la existencia con números."
    if stock > 0 and "initial_stock" not in errors:
        try:
            if _decimal(data.get("initial_cost", "")) <= 0:
                errors["initial_cost"] = "El costo total debe ser mayor que cero."
        except InvalidOperation:
            errors["initial_cost"] = "Escribe el costo total de la existencia inicial."
    try:
        if _decimal(data.get("min_stock", "")) < 0:
            errors["min_stock"] = "El mínimo no puede ser negativo."
    except InvalidOperation:
        errors["min_stock"] = "Escribe el mínimo con números."
    if errors:
        return _dialog_error(request, "catalog/partials/ingredient_form.html", _ingredient_form_context(data, errors))
    response = render(request, "catalog/partials/ingredient_saved.html", {"name": data["name"].strip()})
    response["HX-Trigger"] = "ingredient-created"
    return response
