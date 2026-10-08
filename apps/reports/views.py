"""
Views of M-REP: Caja (WBS 3.5.1, 3.5.7; interface 2.2.4). Owner: Yahir (DEC-31); services: Jared.
Adapted from Yahir's Caja screen (apps/core/templates/caja.html) to base.html and the component library.

CONTRACT DRAFT: every view returns sample data with the exact shape of its context, so the templates can be built and
tested before the services exist (reports/services.py: cash_close, sales_by_period). reports only reads: closing the
shift is pos:close_session. Pending, outside this file:
  - role and PIN checks with the mixin of apps/core/mixins.py (Jesús);
  - the shell context (menu, top bar) from a context processor in apps/core (Jesús);
  - the routes in apps/reports/urls.py (rutas-pendientes.md).
"""
from decimal import Decimal

from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_GET


def _money(amount):
    """$4,850.00 (pantallas-y-patrones.md §4), for labels the server builds, like ticket_label in pos."""
    return f"${amount:,.2f}"


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
    context.update(_shell("cash"))
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
