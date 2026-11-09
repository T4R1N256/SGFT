"""
Views of the Productos screen (WBS 3.2.1–3.2.3; DEC-25). Owner: Tarín (DEC-31); services: Diego.

Dishes, prices, recipes and new ingredients come from the database through apps/catalog/services.py. The whole
screen is admin-only: admin_pin_required asks for the Administrator's PIN and keeps it 30 minutes (DEC-32). The menu
comes from apps.core.context_processors.shell; the cash state of the top bar still comes from apps/core/preview.py
until T18 removes it. catalog depends on no other app (CLAUDE.md §7): it imports neither pos nor inventory.
"""
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_GET, require_http_methods

from apps.catalog import services
from apps.catalog.models import Category, Dish, Ingredient, Recipe, Units
from apps.core import preview
from apps.core.mixins import admin_pin_required

MODULE = "Productos"


def _url(name, *args):
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return "#"


def _decimal(value):
    """Parses what the user typed («$1,250.50», « 3 ») or raises InvalidOperation."""
    return Decimal(str(value).replace("$", "").replace(",", "").strip())


def _shell(request):
    """Top bar of Productos; the menu comes from the context processor."""
    return {"search_placeholder": "Buscar platillo en el catálogo (F2)...", "search_url": _url("catalog:dish_catalog"),
            "search_target": "#dish-grid", "cash_session_open": preview.is_cash_open(request), "session_total": None}


def _emoji(category):
    return category.emoji or category.name[:1].upper()


def _availability(dish):
    """
    What the card badge says, decided here and not in the template: inactive, without a recipe, out of stock
    (some ingredient at 0 or below), few portions (some ingredient at its minimum or below, rule 3) or available.
    """
    if not dish.is_active:
        return "inactivo"
    rows = list(dish.recipes.all())
    if not rows:
        return "sin_receta"
    if any(row.ingredient.stock <= 0 for row in rows):
        return "agotado"
    if any(row.ingredient.stock <= row.ingredient.min_stock for row in rows):
        return "pocas"
    return "disponible"


def _dish(dish):
    return {"id": dish.pk, "name": dish.name, "description": dish.description, "price": dish.price,
            "category": dish.category.name, "category_value": dish.category_id, "emoji": _emoji(dish.category),
            "availability": _availability(dish), "active": dish.is_active,
            "edit_url": _url("catalog:dish_edit", dish.pk), "recipe_url": _url("catalog:recipe_edit", dish.pk)}


def _dishes(query=""):
    dishes = (Dish.objects.select_related("category")
              .prefetch_related(Prefetch("recipes", queryset=Recipe.objects.select_related("ingredient")))
              .order_by("category__name", "name"))
    if query:
        dishes = dishes.filter(name__icontains=query)
    return dishes


def _get_dish(dish_id):
    return _dishes().filter(pk=dish_id).first()


def _grid_context(query=""):
    return {"dishes": [_dish(d) for d in _dishes(query)], "active_count": Dish.objects.filter(is_active=True).count(),
            "create_url": _url("catalog:dish_create")}


def _categories():
    return [{"value": c.pk, "label": c.name, "emoji": _emoji(c)} for c in Category.objects.order_by("name")]


def _ingredients():
    return [{"value": i.pk, "label": i.name, "unit": i.unit} for i in Ingredient.objects.order_by("name")]


def _dialog_error(request, template, context):
    """422 with the same dialog and its errors, retargeted to #dialog so it does not replace the grid."""
    response = render(request, template, context, status=422)
    response["HX-Retarget"] = "#dialog"
    response["HX-Reswap"] = "innerHTML"
    return response


def _not_found(request):
    return render(request, "components/alert.html", {"message": "Ese platillo no existe."}, status=404)


def _field_errors(error, fields):
    """ValidationError of a service → {field: first message}; what has no field of the form goes to form_error."""
    errors, general = {}, []
    for field, messages in getattr(error, "message_dict", {"__all__": error.messages}).items():
        if field in fields:
            errors[field] = messages[0]
        else:
            general.extend(messages)
    return errors, " ".join(general)


# --- Platillos -------------------------------------------------------------------------------------

_DISH_FIELDS = {"name": "name", "category": "category", "price": "price", "description": "description"}


def _dish_form_context(dish=None, data=None, errors=None, form_error=""):
    data = data or {}
    return {
        "dish": dish,
        "post_url": _url("catalog:dish_edit", dish["id"]) if dish else _url("catalog:dish_create"),
        "hx_target": f"#catalog-dish-{dish['id']}" if dish else "#dish-grid",
        "hx_swap": "outerHTML",
        "categories": _categories(),
        "values": {
            "name": data.get("name", dish["name"] if dish else ""),
            "category": data.get("category", dish["category_value"] if dish else ""),
            "price": data.get("price", dish["price"] if dish else None),
            "description": data.get("description", dish["description"] if dish else ""),
            "active": data.get("active", "") if data else (dish["active"] if dish else True),
        },
        "errors": errors or {},
        "form_error": form_error,
    }


def _clean_dish(data):
    """Turns the form into the service's arguments. Returns (fields, errors); the service checks the rest."""
    errors, fields = {}, {}
    fields["name"] = data.get("name", "").strip()
    if not fields["name"]:
        errors["name"] = "Escribe el nombre del platillo."
    category = str(data.get("category", ""))
    fields["category"] = Category.objects.filter(pk=category).first() if category.isdigit() else None
    if fields["category"] is None:
        errors["category"] = "Elige una categoría."
    try:
        fields["price"] = _decimal(data.get("price", ""))
        if fields["price"] <= 0:
            errors["price"] = "El precio debe ser mayor que cero."
        elif fields["price"] != fields["price"].quantize(Decimal("0.01")):
            errors["price"] = "El precio admite dos decimales como máximo."
    except InvalidOperation:
        errors["price"] = "Escribe el precio con números, por ejemplo 75.00."
    fields["description"] = data.get("description", "").strip()
    if len(fields["description"]) > 120:
        errors["description"] = "La descripción admite 120 caracteres como máximo."
    fields["is_active"] = "active" in data
    return fields, errors


@admin_pin_required(MODULE)
@require_GET
def dish_catalog(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.1                      DEC-25
    URL name    : catalog:dish_catalog       Método: GET (carga completa o HTMX); parámetro q (búsqueda)
    Roles       : admin, con PIN de Administrador (admin_pin_required)
    Plantilla   : catalog/products.html [página] · catalog/partials/dish_grid.html [fragmento, si request.htmx]
    HTMX        : el buscador hace hx-get con hx-target="#dish-grid" hx-swap="outerHTML"
    Contexto    :
        dishes        list  {id, name, description, price: Decimal, category, category_value, emoji,
                             availability: "disponible"|"pocas"|"agotado"|"sin_receta"|"inactivo", active: bool,
                             edit_url, recipe_url}
                            availability la decide el servidor con las existencias de la receta
        active_count  int   platillos activos (subtítulo)
        create_url    str   diálogo «Agregar platillo» (botón a la derecha del encabezado)
        + menú (procesador de contexto) y barra superior
    Controles (HATEOAS):
        edit_url / recipe_url / create_url presentes -> «Editar», «Receta», botón «Agregar platillo»
    Errores     : 403 sin PIN (diálogo del PIN)
    """
    query = request.GET.get("q", "").strip()
    context = {**_shell(request), **_grid_context(query)}
    template = "catalog/partials/dish_grid.html" if request.htmx else "catalog/products.html"
    return render(request, template, context)


@admin_pin_required(MODULE)
@require_http_methods(["GET", "POST"])
def dish_create(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.1                      Regla 6
    URL name    : catalog:dish_create        Método: GET (diálogo) · POST (guarda con services.create_dish)
    Roles       : admin, con PIN
    Plantilla   : GET y 422 → catalog/partials/dish_form.html [fragmento, diálogo en #dialog]
                  POST válido → catalog/partials/dish_grid.html [fragmento] + cierre del diálogo (hx-swap-oob)
    HTMX        : el formulario hace hx-post con hx-target="#dish-grid" hx-swap="outerHTML"
    Contexto    : dish: None, post_url, hx_target, hx_swap, categories: list {value: pk, label, emoji},
                  values: {name, category, price, description, active}, errors: {campo: mensaje}, form_error
                  La receta se edita aparte, con catalog:recipe_edit (botón «Receta» de cada tarjeta).
    Errores     : 422 con el diálogo y el error bajo cada campo (HX-Retarget="#dialog")
    """
    if request.method == "GET":
        return render(request, "catalog/partials/dish_form.html", _dish_form_context())
    fields, errors = _clean_dish(request.POST)
    if not errors:
        try:
            services.create_dish(**fields)
        except ValidationError as error:
            errors, form_error = _field_errors(error, _DISH_FIELDS)
            return _dialog_error(request, "catalog/partials/dish_form.html",
                                 _dish_form_context(data=request.POST, errors=errors, form_error=form_error))
        return render(request, "catalog/partials/dish_grid.html", {**_grid_context(), "close_dialog": True})
    return _dialog_error(request, "catalog/partials/dish_form.html",
                         _dish_form_context(data=request.POST, errors=errors))


@admin_pin_required(MODULE)
@require_http_methods(["GET", "POST"])
def dish_edit(request, dish_id):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.1                      Reglas 6 y 14 (lo ya cobrado conserva su precio)
    URL name    : catalog:dish_edit          Método: GET (diálogo) · POST (guarda con services.update_dish)
    Roles       : admin, con PIN
    Plantilla   : GET y 422 → catalog/partials/dish_form.html [fragmento, diálogo en #dialog]
                  POST válido → catalog/partials/dish_card.html [fragmento] + cierre del diálogo (hx-swap-oob)
    HTMX        : el formulario hace hx-post con hx-target="#catalog-dish-<id>" hx-swap="outerHTML"
    Contexto    : como catalog:dish_create, con dish (el platillo) y values prellenados; tras guardar, dish
                  Desmarcar «Activo en el menú» lo quita de Nueva venta; un platillo nunca se borra.
    Errores     : 404 si el platillo no existe · 422 como en catalog:dish_create
    """
    instance = _get_dish(dish_id)
    if instance is None:
        return _not_found(request)
    dish = _dish(instance)
    if request.method == "GET":
        return render(request, "catalog/partials/dish_form.html", _dish_form_context(dish))
    fields, errors = _clean_dish(request.POST)
    if not errors:
        try:
            services.update_dish(instance, **fields)
        except ValidationError as error:
            errors, form_error = _field_errors(error, _DISH_FIELDS)
            return _dialog_error(request, "catalog/partials/dish_form.html",
                                 _dish_form_context(dish, request.POST, errors, form_error))
        return render(request, "catalog/partials/dish_card.html",
                      {"dish": _dish(_get_dish(dish_id)), "close_dialog": True})
    return _dialog_error(request, "catalog/partials/dish_form.html", _dish_form_context(dish, request.POST, errors))


# --- Recetas ---------------------------------------------------------------------------------------

def _recipe_line(index, ingredient_id="", quantity="", error="", units=None):
    units = units if units is not None else {}
    return {"index": index, "ingredient": ingredient_id, "quantity": quantity,
            "unit": units.get(str(ingredient_id), ""), "error": error}


def _quantity_label(value):
    """0.150 → 0.15 and 1.000 → 1, as the Administrator would write it."""
    value = value.normalize()
    return str(value.quantize(Decimal(1)) if value == value.to_integral() else value)


@admin_pin_required(MODULE)
@require_http_methods(["GET", "POST"])
def recipe_edit(request, dish_id):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.3                      DEC-25, regla 6
    URL name    : catalog:recipe_edit        Método: GET (diálogo) · POST (reemplaza la receta con services.set_recipe)
    Roles       : admin, con PIN
    Plantilla   : GET y 422 → catalog/partials/recipe_form.html [fragmento, diálogo en #dialog]
                  POST válido → catalog/partials/recipe_saved.html: aviso en #messages, cierre del diálogo
                  (hx-swap-oob) y la tarjeta del platillo fuera de banda, porque su disponibilidad depende de la receta
    HTMX        : hx-post con hx-target="#messages" hx-swap="afterbegin"
    Contexto    : dish, post_url, hx_target, hx_swap, add_line_url, ingredients: list {value, label, unit},
                  lines: list {index, ingredient, quantity, unit, error}, next_index: int, form_error: str
                  Cada fila envía ingredient_<n> y quantity_<n>; la unidad la decide el insumo (no se edita).
    Errores     : 404 si el platillo no existe · 422 con el diálogo: insumo repetido, cantidad no positiva o
                  receta vacía. La receta se guarda completa o no se guarda.
    """
    instance = _get_dish(dish_id)
    if instance is None:
        return _not_found(request)
    dish = _dish(instance)
    ingredients = _ingredients()
    units = {str(i["value"]): i["unit"] for i in ingredients}
    base = {"dish": dish, "post_url": _url("catalog:recipe_edit", dish_id),
            "add_line_url": _url("catalog:add_recipe_line"), "ingredients": ingredients,
            "hx_target": "#messages", "hx_swap": "afterbegin"}
    if request.method == "GET":
        rows = sorted(instance.recipes.all(), key=lambda row: row.ingredient.name)
        lines = [_recipe_line(i, row.ingredient_id, _quantity_label(row.quantity), units=units)
                 for i, row in enumerate(rows)]
        return render(request, "catalog/partials/recipe_form.html", {**base, "lines": lines, "next_index": len(lines)})

    indexes = sorted({int(k.split("_")[1]) for k in request.POST
                      if k.startswith("ingredient_") and k.split("_")[1].isdigit()})
    by_pk = Ingredient.objects.in_bulk([request.POST.get(f"ingredient_{i}") for i in indexes
                                        if request.POST.get(f"ingredient_{i}", "").isdigit()])
    lines, items, seen, has_error = [], [], set(), False
    for i in indexes:
        ingredient_id, quantity = request.POST.get(f"ingredient_{i}", ""), request.POST.get(f"quantity_{i}", "").strip()
        ingredient = by_pk.get(int(ingredient_id)) if ingredient_id.isdigit() else None
        error = ""
        try:
            if ingredient is None:
                error = "Elige un insumo."
            elif ingredient_id in seen:
                error = "Ese insumo ya está en la receta."
            elif _decimal(quantity) <= 0:
                error = "La cantidad debe ser mayor que cero."
            elif _decimal(quantity) != _decimal(quantity).quantize(Decimal("0.001")):
                error = "La cantidad admite tres decimales como máximo."
            else:
                items.append((ingredient, _decimal(quantity)))
        except InvalidOperation:
            error = "Escribe la cantidad con números."
        seen.add(ingredient_id)
        has_error = has_error or bool(error)
        lines.append(_recipe_line(i, ingredient_id, quantity, error, units))
    next_index = (indexes[-1] + 1) if indexes else 0
    form_error = "" if lines else "Agrega al menos un insumo a la receta."
    if not has_error and lines:
        try:
            services.set_recipe(instance, items)
        except ValidationError as error:
            form_error = " ".join(error.messages)
    if has_error or form_error:
        return _dialog_error(request, "catalog/partials/recipe_form.html",
                             {**base, "lines": lines, "next_index": next_index, "form_error": form_error})
    return render(request, "catalog/partials/recipe_saved.html", {"dish": _dish(_get_dish(dish_id))})


@admin_pin_required(MODULE)
@require_GET
def add_recipe_line(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.3
    URL name    : catalog:add_recipe_line    Método: GET (HTMX); parámetro index
    Roles       : admin, con PIN
    Plantilla   : catalog/partials/recipe_line.html [fragmento] — una fila vacía, más fuera de banda el botón
                  «Agregar insumo» con el índice siguiente y la eliminación del aviso de receta vacía
    HTMX        : «Agregar insumo» hace hx-get con hx-target="#recipe-lines" hx-swap="beforeend"
    Contexto    : line: {index, ingredient: "", quantity: "", unit: "", error: ""}, ingredients,
                  add_line_url, next_index: int, oob: True
    """
    try:
        index = max(int(request.GET.get("index", "0")), 0)
    except ValueError:
        index = 0
    return render(request, "catalog/partials/recipe_line.html",
                  {"line": _recipe_line(index), "ingredients": _ingredients(),
                   "add_line_url": _url("catalog:add_recipe_line"), "next_index": index + 1, "oob": True})


# --- Insumos ---------------------------------------------------------------------------------------

_UNITS = [{"value": value, "label": value} for value in Units.values]
_INGREDIENT_FIELDS = ("name", "unit", "min_stock")


def _ingredient_form_context(data=None, errors=None, form_error=""):
    data = data or {}
    return {"post_url": _url("catalog:ingredient_create"), "hx_target": "#messages", "hx_swap": "afterbegin",
            "units": _UNITS, "values": {k: data.get(k, "") for k in _INGREDIENT_FIELDS},
            "errors": errors or {}, "form_error": form_error}


@admin_pin_required("Inventario")
@require_http_methods(["GET", "POST"])
def ingredient_create(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.2.2                      Reglas 3 y 6
    URL name    : catalog:ingredient_create  Método: GET (diálogo) · POST (da de alta con services.create_ingredient)
    Roles       : admin, con PIN (se abre desde Inventario, que ya lo pidió; DEC-32)
    Plantilla   : GET y 422 → catalog/partials/ingredient_form.html [fragmento, diálogo en #dialog]
                  POST válido → catalog/partials/ingredient_saved.html [fragmento]: aviso en #messages y cierre del
                  diálogo (hx-swap-oob), más el evento HX-Trigger «ingredient-created» para que Inventario (Yahir)
                  refresque su rejilla sin que catalog dependa de inventory.
    HTMX        : el tile «Agregar insumo» de Inventario hace hx-get con hx-target="#dialog";
                  el formulario hace hx-post con hx-target="#messages" hx-swap="afterbegin"
    Contexto    : post_url, hx_target, hx_swap, units: list {value, label}, values: {name, unit, min_stock},
                  errors: {campo: mensaje}, form_error
    Reglas      : la unidad se fija al dar de alta el insumo (compras, mermas y recetas la toman de ahí). El insumo
                  nace con existencia 0: la existencia y el costo entran con la primera compra en Inventario
                  (inventory.register_purchase), porque catalog no importa inventory y la existencia solo cambia
                  con un movimiento.
    Errores     : 422 con el diálogo y el error bajo cada campo (HX-Retarget="#dialog")
    """
    if request.method == "GET":
        return render(request, "catalog/partials/ingredient_form.html", _ingredient_form_context())
    data, errors = request.POST, {}
    name = data.get("name", "").strip()
    if not name:
        errors["name"] = "Escribe el nombre del insumo."
    if data.get("unit") not in Units.values:
        errors["unit"] = "Elige la unidad de medida."
    min_stock = None
    try:
        min_stock = _decimal(data.get("min_stock", ""))
        if min_stock < 0:
            errors["min_stock"] = "El mínimo no puede ser negativo."
        elif min_stock != min_stock.quantize(Decimal("0.001")):
            errors["min_stock"] = "El mínimo admite tres decimales como máximo."
    except InvalidOperation:
        errors["min_stock"] = "Escribe el mínimo con números."
    if not errors:
        try:
            services.create_ingredient(name, data["unit"], min_stock=min_stock)
        except ValidationError as error:
            errors, form_error = _field_errors(error, _INGREDIENT_FIELDS)
            return _dialog_error(request, "catalog/partials/ingredient_form.html",
                                 _ingredient_form_context(data, errors, form_error))
        response = render(request, "catalog/partials/ingredient_saved.html", {"name": name})
        response["HX-Trigger"] = "ingredient-created"
        return response
    return _dialog_error(request, "catalog/partials/ingredient_form.html", _ingredient_form_context(data, errors))
