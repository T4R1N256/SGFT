"""
Views of M-REP: Caja y Reportes (WBS 3.5.1–3.5.7; interface 2.2.4). Owner: Yahir (DEC-31); services: Jared.
Adapted from Yahir's Caja and Reportes screens (apps/core/templates/caja.html, reportes.html) to base.html and the
component library.

The numbers come from reports/services.py (cash_close, sales_by_period, top_dishes, ingredients_used,
waste_by_period, profit, export_daily_sales_pdf); these views only pick the period and format labels. reports only
reads: closing the shift is pos:close_session. The menu comes from apps.core.context_processors.shell.
"""
from datetime import date
from decimal import Decimal

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.core.mixins import admin_pin_required
from apps.pos.services_cash_session import current_session
from apps.reports import services

MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
          "noviembre", "diciembre"]
DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
SCALES = [Decimal(n) for n in (500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000)]


def _money(amount):
    """$4,850.00 (pantallas-y-patrones.md §4), for labels the server builds."""
    return f"${amount:,.2f}"


def _quantity(value):
    value = value.normalize()
    return value.quantize(Decimal(1)) if value == value.to_integral() else value


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


def _period(request, default):
    period = request.GET.get("periodo", default)
    return period if period in services.PERIODS else default


def _trend(current, previous, against):
    """«+8.3% vs ayer»; without a previous amount there is nothing to compare."""
    if not previous:
        return f"Sin ventas {against}" if current else ""
    change = (current - previous) / previous * 100
    return f"{change:+.1f}% {against}"


def _share(amount, sales):
    return f"{amount / sales * 100:.1f}% de ventas" if sales else "Sin ventas"


def _shell(request):
    """Top bar without search (plan de interfaz §2); the cash state is the real open session."""
    session = current_session()
    return {"hide_search": True, "cash_session_open": session is not None,
            "session_total": services.cash_close(session)["total"] if session else None}


def _chart(bars):
    """Heights in % of a round scale and the highest bar active; no bars when nothing was sold."""
    if not bars or not any(amount for _, amount in bars):
        return {"bars": [], "axis": []}
    top = max(amount for _, amount in bars)
    scale = next((s for s in SCALES if top <= s), top)
    peak = max(range(len(bars)), key=lambda i: bars[i][1])
    return {"bars": [{"label": label, "amount": amount, "pct": round(amount / scale * 100), "active": i == peak}
                     for i, (label, amount) in enumerate(bars)],
            "axis": [scale, scale / 2, Decimal(0)]}


def _chart_labels(period, bars):
    return [(f"{label} h" if period == "hoy" else label, amount) for label, amount in bars]


def _period_chips(period, url, target):
    return [{"text": t, "active": k == period, "hx_get": f"{url}?periodo={k}", "hx_target": target}
            for k, t in (("hoy", "Hoy"), ("semana", "Semana"), ("mes", "Mes"))]


# ------------------------------------------------------------------------------------------------ Caja

@admin_pin_required("Caja")
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
        subtitle         str      turno, apertura y fondo inicial, o «No hay un turno de caja abierto»
        chart            {bars: [{label, amount, pct, active}], axis: [Decimal]}   alturas en % del servidor
        chips            list     {text, active, hx_get, hx_target}
        profit           {amount, trend, note}          ventas de hoy − costo de insumos por receta
        waste            {amount, share, note}          mermas de hoy
        today            {total, cash_label, transfer_label}
        close            {expected_amount, pending_sync, url}  url vacío sin turno abierto: no hay «Cerrar caja»
    Controles   : «Cerrar caja» (Primario, sin candado: el PIN ya se pidió al entrar) solo con turno abierto.
    Vacío       : sin ventas en el periodo, «Sin ventas para este periodo» centrado
    """
    period = _period(request, "hoy")
    today = timezone.localdate()
    url = _url("reports:cash")
    bars = services.sales_by_period(*services.period_range(period, today))["chart"]
    context = {"chart": _chart(_chart_labels(period, bars)), "chips": _period_chips(period, url, "#sales-chart")}
    if request.htmx and not request.htmx.boosted:
        return render(request, "reports/partials/sales_chart.html", context)

    session = current_session()
    sales = services.sales_by_period(today, today)
    yesterday = services.sales_by_period(*services.previous_range(today, today))
    profit = services.profit(today, today)
    waste = services.waste_by_period(today, today)
    if session:
        opened = timezone.localtime(session.server_timestamp)
        subtitle = (f"Turno del {session.business_date:%d/%m/%Y} · Abierta desde las {opened:%H:%M} · "
                    f"Fondo inicial {_money(session.opening_amount)}")
        close = {"expected_amount": services.cash_close(session)["expected_amount"], "url": _url("pos:close_session")}
    else:
        subtitle, close = "No hay un turno de caja abierto", {"expected_amount": Decimal("0.00"), "url": ""}
    pending = request.GET.get("pendientes", "0")  # the device counts its queue; the server cannot know it
    close["pending_sync"] = int(pending) if pending.isdigit() else 0
    margin = f" · Margen del {profit['margin']}%" if profit["margin"] is not None else ""
    biggest = waste["items"][0] if waste["items"] else None
    registros = "registro" if waste["count"] == 1 else "registros"
    context.update(_shell(request))
    context.update({
        "subtitle": subtitle,
        "profit": {"amount": profit["amount"], "trend": _trend(sales["total"], yesterday["total"], "vs ayer"),
                   "note": f"Ventas {_money(profit['sales'])} − costo de insumos por receta "
                           f"{_money(profit['cost'])}{margin}"},
        "waste": {"amount": waste["cost"], "share": _share(waste["cost"], sales["total"]),
                  "note": f"{waste['count']} {registros} hoy" + (
                      f" · Mayor merma: {biggest['name'].lower()} ({_money(biggest['cost'])}, "
                      f"{biggest['reason'].lower()})" if biggest else "")},
        "today": {"total": sales["total"], "cash_label": _money(sales["cash"]),
                  "transfer_label": _money(sales["transfer"])},
        "close": close,
    })
    return render(request, "reports/cash.html", context)


# ------------------------------------------------------------------------------------------------ Reportes

def _labels(period, first, last):
    """(subtitle, range) of the period, in Spanish."""
    if period == "hoy":
        return (f"{DAYS[first.weekday()]} {first.day} de {MONTHS[first.month - 1]} de {first.year} · Corte del día",
                f"{first:%d/%m/%Y}")
    if period == "semana":
        if first.month == last.month:
            text = f"Semana del {first.day} al {last.day} de {MONTHS[last.month - 1]} de {last.year}"
        else:
            text = f"Semana del {first.day} de {MONTHS[first.month - 1]} al {last.day} de {MONTHS[last.month - 1]}" \
                   f" de {last.year}"
        return f"{text} · Corte semanal", f"{first:%d/%m/%Y} – {last:%d/%m/%Y}"
    return (f"{MONTHS[first.month - 1].capitalize()} de {first.year} · Corte mensual",
            f"{first:%d/%m/%Y} – {last:%d/%m/%Y}")


def _report(period, first, last):
    sales = services.sales_by_period(first, last)
    waste = services.waste_by_period(first, last)
    if not sales["tickets"] and not sales["cancelled"] and not waste["count"]:
        return {"empty": True}
    previous = services.sales_by_period(*services.previous_range(first, last))
    against = {"hoy": "vs ayer", "semana": "vs semana anterior", "mes": "vs mes anterior"}[period]
    top = services.top_dishes(first, last)
    best = top[0]["units"] if top else 1
    used = services.ingredients_used(first, last)
    return {
        "empty": False,
        "sales": {"total": sales["total"], "trend": _trend(sales["total"], previous["total"], against),
                  "cash_label": _money(sales["cash"]), "transfer_label": _money(sales["transfer"]),
                  "tickets_label": f"Tickets: {sales['tickets']}",
                  "average_label": f"Promedio {_money(sales['average'])}"},
        "chart": _chart(_chart_labels(period, sales["chart"])),
        "waste": {"total": waste["cost"], "share": _share(waste["cost"], sales["total"]),
                  "items": [{"name": i["name"], "reason": i["reason"], "cost_label": _money(i["cost"])}
                            for i in waste["items"][:6]]},
        "top_dishes": [{"rank": n, "name": d["name"], "units_label": f"{d['units']} uds.",
                        "pct": round(d["units"] / best * 100)} for n, d in enumerate(top, start=1)],
        "top_label": f"Total vendido (top {len(top)})", "top_units_label": f"{sum(d['units'] for d in top)} uds.",
        "ingredients_used": [{"emoji": i["name"][:1].upper(), "name": i["name"],
                              "cost_label": f"Costo {_money(i['cost'])}",
                              "quantity": f"{_quantity(i['quantity'])} {i['unit']}"} for i in used["items"]],
        "ingredients_label": f"Costo de insumos (top {len(used['items'])})",
        "ingredients_cost_label": _money(used["cost"]),
    }


@admin_pin_required("Reportes")
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
        subtitle   str      periodo; con HTMX se reemplaza fuera de banda (oob_subtitle)
        range_label str     «02/11/2026 – 08/11/2026»
        chips, date_value (date), export_url («Exportar PDF» abre el diálogo en #dialog)
    Vacío       : «Sin ventas para este periodo» centrado en las cuatro columnas
    """
    period = _period(request, "semana")
    day = _date(request.GET.get("fecha"), timezone.localdate())
    first, last = services.period_range(period, day)
    subtitle, range_label = _labels(period, first, last)
    url = _url("reports:reports")
    context = {"report": _report(period, first, last), "period_label": subtitle, "range_label": range_label,
               "chips": _period_chips(period, url, "#report-columns"), "period": period, "date_value": day,
               "list_url": url, "subtitle": subtitle}
    if request.htmx and not request.htmx.boosted:
        return render(request, "reports/partials/report_columns.html", {**context, "oob_subtitle": True})
    context.update(_shell(request))
    context["export_url"] = _url("reports:export_daily_sales_pdf")
    return render(request, "reports/reports.html", context)


@admin_pin_required("Reportes")
@require_GET
def export_daily_sales_pdf(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.5.5
    URL name  : reports:export_daily_sales_pdf
    Roles     : admin (con PIN)
    GET con HTMX → reports/partials/export_pdf_form.html [#dialog], con el día de hoy
    GET normal con «day» (AAAA-MM-DD) → descarga «ventas-AAAA-MM-DD.pdf» (servicio export_daily_sales_pdf)
    """
    today = timezone.localdate()
    if request.htmx:
        return render(request, "reports/partials/export_pdf_form.html",
                      {"day": _date(request.GET.get("day"), today), "method": "get",
                       "post_url": _url("reports:export_daily_sales_pdf")})
    day = _date(request.GET.get("day"), today)
    response = HttpResponse(services.export_daily_sales_pdf(day), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="ventas-{day:%Y-%m-%d}.pdf"'
    return response
