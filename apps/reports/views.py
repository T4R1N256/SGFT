"""
Views of M-REP: Caja y Reportes (WBS 3.5.1–3.5.7; interface 2.2.4). Owner: Yahir (DEC-31); services: Jared.
Adapted from Yahir's Caja and Reportes screens (apps/core/templates/caja.html, reportes.html) to base.html and the
component library.

CONTRACT DRAFT: every view returns sample data with the exact shape of its context, so the templates can be built and
tested before the services exist (reports/services.py: cash_close, sales_by_period, top_dishes,
export_daily_sales_pdf). reports only reads: closing the
shift is pos:close_session. Pending, outside this file:
  - role and PIN checks with the mixin of apps/core/mixins.py (Jesús);
  - the shell context (menu, top bar) from a context processor in apps/core (Jesús);
  - the routes in apps/reports/urls.py (rutas-pendientes.md).
"""
from datetime import date
from decimal import Decimal

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_GET

from apps.core import preview


def _money(amount):
    """$4,850.00 (pantallas-y-patrones.md §4), for labels the server builds, like ticket_label in pos."""
    return f"${amount:,.2f}"


def _date(value, default):
    try:
        return date.fromisoformat(value) if value else default
    except ValueError:
        return default


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


# ------------------------------------------------------------------------------------------------ Caja

_HOURLY = [("07", 180), ("08", 620), ("09", 890), ("10", 540), ("11", 310), ("12", 460), ("13", 720), ("14", 500),
           ("15", 390), ("16", 240)]  # suma $4,850 (pantallas-y-patrones.md §5)
_WEEK = [("L", 3980), ("M", 4410), ("M", 4120), ("J", 4630), ("V", 5480), ("S", 4720), ("D", 4210)]
_MONTH = [("S1", 28900), ("S2", 30120), ("S3", 31550), ("S4", 29840)]


def _chart(period):
    rows, unit = {"hoy": (_HOURLY, " h"), "semana": (_WEEK, ""), "mes": (_MONTH, "")}[period]
    if not rows:
        return {"bars": [], "axis": []}
    top = max(v for _, v in rows)
    scale = 1000 if top <= 1000 else 6000 if top <= 6000 else 40000
    peak = max(range(len(rows)), key=lambda i: rows[i][1])
    bars = [{"label": f"{l}{unit}", "amount": Decimal(v), "pct": round(v / scale * 100), "active": i == peak}
            for i, (l, v) in enumerate(rows)]
    return {"bars": bars, "axis": [Decimal(scale), Decimal(scale // 2), Decimal(0)]}


def _period_chips(period, url, target):
    return [{"text": t, "active": k == period, "hx_get": f"{url}?periodo={k}", "hx_target": target}
            for k, t in (("hoy", "Hoy"), ("semana", "Semana"), ("mes", "Mes"))]


@preview.require_admin_pin("Caja", lambda request: preview.apply_to_shell(request, _shell("cash")))
@require_GET
def cash(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.5.1, 3.5.7 · interfaz 2.2.4
    URL name    : reports:cash      Método: GET
    Roles       : admin (con PIN; el desbloqueo dura 30 minutos)
    Plantilla   : request.htmx → reports/partials/sales_chart.html [fragmento, id «sales-chart»]
                  si no → reports/cash.html [página completa]
    HTMX        : chips Hoy / Semana / Mes con hx-get «?periodo=…» y hx-target="#sales-chart"
    Contexto    :
        subtitle         str      turno, apertura, fondo inicial y «Última sincronización» (sin red, los datos son de
                                  la última sincronización)
        chart            {bars: [{label, amount, pct, active}], axis: [Decimal]}   alturas en % del servidor
        chips            list     {text, active, hx_get, hx_target}
        profit           {amount, trend, note}          components/kpi.html
        waste            {amount, share, note}          components/kpi.html
        today            {total, cash_label, transfer_label}   components/key_value.html
        close            {expected_amount, pending_sync, url}  «Cerrar caja» abre pos:close_session en #dialog
    Controles   : «Cerrar caja» (Primario, sin candado: el PIN ya se pidió al entrar). Sin buscador.
    Vacío       : sin ventas en el periodo, «Sin ventas para este periodo» centrado (?estado=vacio)
    """
    period = request.GET.get("periodo", "hoy")
    period = period if period in ("hoy", "semana", "mes") else "hoy"
    url = _url("reports:cash")
    chart = {"bars": [], "axis": []} if request.GET.get("estado") == "vacio" else _chart(period)
    context = {"chart": chart, "chips": _period_chips(period, url, "#sales-chart")}
    if request.htmx and not request.htmx.boosted:
        return render(request, "reports/partials/sales_chart.html", context)
    context.update(preview.apply_to_shell(request, _shell("cash")))
    context.update({
        "subtitle": f"Turno matutino · Abierta desde las 7:00 AM · Fondo inicial {_money(Decimal('500'))} · Última sincronización: hoy, 10:45 AM",
        "profit": {"amount": Decimal("2910.00"), "trend": "+8.3% vs ayer",
                   "note": f"Ventas {_money(Decimal('4850'))} − costo de insumos por receta {_money(Decimal('1940'))} · Margen del 60%"},
        "waste": {"amount": Decimal("186.50"), "share": "3.8% de ventas",
                  "note": "5 registros hoy · Mayor merma: carne asada ($84.00, caducidad)"},
        "today": {"total": Decimal("4850.00"), "cash_label": _money(Decimal("3120")), "transfer_label": _money(Decimal("1730"))},
        "close": {"expected_amount": Decimal("3620.00"), "pending_sync": int(request.GET.get("pendientes", 0)),
                  "url": _url("pos:close_session")},
    })
    return render(request, "reports/cash.html", context)


# ------------------------------------------------------------------------------------------------ Reportes

def _report(period, empty=False):
    if empty:
        return {"empty": True}
    return {
        "empty": False,
        "ingredients_used": [{"emoji": e, "name": n, "cost_label": f"Costo {_money(Decimal(c))}", "quantity": q} for e, n, c, q in [
            ("🌮", "Tortilla de harina", "1224", "612 pzas"), ("🥩", "Carne asada", "4048", "18.4 kg"),
            ("🍗", "Pollo deshebrado", "1638", "12.6 kg"), ("🧀", "Queso chihuahua", "1264", "7.9 kg"),
            ("🥣", "Frijol refrito", "368", "9.2 kg"), ("🥚", "Huevo", "288", "96 pzas"), ("☕", "Café molido", "400", "1.6 kg")]],
        "ingredients_label": "Costo de insumos (top 7)", "ingredients_cost_label": _money(Decimal("9230")),
        "top_dishes": [{"rank": i + 1, "name": n, "units_label": f"{u} uds.", "pct": round(u / 214 * 100)} for i, (n, u) in enumerate([
            ("Burrito de asada", 214), ("Burrito de pollo", 176), ("Chilaquiles verdes", 98), ("Café de olla", 91),
            ("Machaca con huevo", 77), ("Frijol con queso", 64)])],
        "top_label": "Total vendido (top 6)", "top_units_label": "720 uds.",
        "sales": {"total": Decimal("31550.00"), "trend": "+6.1% vs semana anterior", "cash_label": _money(Decimal("20450")),
                  "transfer_label": _money(Decimal("11100")), "tickets_label": "Tickets: 254",
                  "average_label": f"Promedio {_money(Decimal('124.21'))}"},
        "chart": _chart("semana"),
        "waste": {"total": Decimal("742.00"), "share": "2.4% de ventas", "items": [
            {"name": n, "reason": r, "cost_label": _money(Decimal(c))} for n, r, c in [
                ("Carne asada", "Caducidad", "210"), ("Queso chihuahua", "Mal almacenamiento", "168"),
                ("Tortilla de harina", "Daño en empaque", "108"), ("Pollo deshebrado", "Caducidad", "96"),
                ("Aguacate", "Maduración", "90"), ("Salsa verde", "Caducidad", "70")]]},
    }


@preview.require_admin_pin("Reportes", lambda request: preview.apply_to_shell(request, _shell("reports")))
@require_GET
def reports(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.5.2–3.5.4 · interfaz 2.2.4
    URL name    : reports:reports      Método: GET (?periodo=hoy|semana|mes&fecha=AAAA-MM-DD)
    Roles       : admin (con PIN)
    Plantilla   : request.htmx → reports/partials/report_columns.html [fragmento, id «report-columns»]
                  si no → reports/reports.html [página completa]
    HTMX        : chips y campo de fecha con hx-get, hx-target="#report-columns" y hx-push-url
    Contexto    :
        report     {empty, sales, chart, waste, top_dishes, top_label, top_units_label, ingredients_used,
                    ingredients_label, ingredients_cost_label} — textos ya formateados para los componentes
        subtitle   str      periodo y «Última sincronización»; con HTMX se reemplaza fuera de banda (oob_subtitle)
        range_label str     «21/09/2026 – 27/09/2026»
        chips, date_value (date), export_url («Exportar PDF» abre el diálogo en #dialog)
    Vacío       : «Sin ventas para este periodo» centrado en las cuatro columnas (?estado=vacio)
    """
    period = request.GET.get("periodo", "semana")
    period = period if period in ("hoy", "semana", "mes") else "semana"
    labels = {"hoy": ("Domingo 27 de septiembre de 2026 · Corte del día", "27/09/2026"),
              "semana": ("Semana del 21 al 27 de septiembre de 2026 · Corte semanal", "21/09/2026 – 27/09/2026"),
              "mes": ("Septiembre de 2026 · Corte mensual", "01/09/2026 – 30/09/2026")}[period]
    url = _url("reports:reports")
    context = {"report": _report(period, empty=request.GET.get("estado") == "vacio"), "period_label": labels[0],
               "range_label": labels[1], "chips": _period_chips(period, url, "#report-columns"), "period": period,
               "date_value": _date(request.GET.get("fecha"), date(2026, 9, 21)), "list_url": url,
               "subtitle": f"{labels[0]} · Última sincronización: hoy, 10:45 AM"}
    if request.htmx and not request.htmx.boosted:
        return render(request, "reports/partials/report_columns.html", {**context, "oob_subtitle": True})
    context.update(preview.apply_to_shell(request, _shell("reports")))
    context["export_url"] = _url("reports:export_daily_sales_pdf")
    return render(request, "reports/reports.html", context)


@preview.require_admin_pin("Reportes", lambda request: preview.apply_to_shell(request, _shell("reports")))
@require_GET
def export_daily_sales_pdf(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    URL name  : reports:export_daily_sales_pdf
    GET con HTMX → reports/partials/export_pdf_form.html [#dialog]; GET normal con «day» → descarga el PDF
    (borrador: devuelve un texto en lugar del PDF; el servicio export_daily_sales_pdf es de Jared)
    """
    if request.htmx:
        return render(request, "reports/partials/export_pdf_form.html",
                      {"day": _date(request.GET.get("day"), date(2026, 9, 27)), "method": "get",
                       "post_url": _url("reports:export_daily_sales_pdf")})
    return HttpResponse(f"Borrador: aquí se descargaría el PDF de las ventas del {request.GET.get('day', '')}.",
                        content_type="text/plain; charset=utf-8")
