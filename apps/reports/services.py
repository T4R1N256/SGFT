"""
Reports: cash close, sales by period, best sellers, ingredients used, waste and the daily sales PDF (WBS 3.5.2–3.5.5).
Owner: Jared.

reports only reads (CLAUDE.md §7): it has no models and never writes. Everything comes from what was recorded
(rule 5): a sale counts what was charged minus what its cancellations and adjustments reverted, and a payment
correction moves it to the new method (rule 11). The functions return numbers (Decimal, int); the views format them.

A sale belongs to the day and hour of its device timestamp, in Ciudad Juárez time: an offline sale counts when it
was charged, not when it synced.
"""
from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal
from io import BytesIO

from django.db.models import Prefetch
from django.utils import timezone

from apps.inventory.models import MovementKind, StockMovement
from apps.pos.models import AdjustmentKind, AdjustmentReason, OrderItem, PaymentMethod, Sale, SessionStatus
from apps.pos.services_cash_session import expected_cash, sales_totals

ZERO = Decimal("0.00")
PERIODS = ("hoy", "semana", "mes")
WEEKDAYS = ["L", "M", "M", "J", "V", "S", "D"]


# ---------- Periodos ----------
def period_range(period, day=None):
    """(first, last) dates of the period that contains day: hoy is that day, semana Monday–Sunday, mes the month."""
    day = day or timezone.localdate()
    if period == "semana":
        first = day - timedelta(days=day.weekday())
        return first, first + timedelta(days=6)
    if period == "mes":
        first = day.replace(day=1)
        following = (first + timedelta(days=32)).replace(day=1)
        return first, following - timedelta(days=1)
    return day, day


def previous_range(first, last):
    """The period of the same length right before (for «vs semana anterior»)."""
    days = (last - first).days + 1
    return first - timedelta(days=days), first - timedelta(days=1)


def _bounds(first, last):
    tz = timezone.get_current_timezone()
    return (timezone.make_aware(datetime.combine(first, time.min), tz),
            timezone.make_aware(datetime.combine(last + timedelta(days=1), time.min), tz))


# ---------- Ventas netas ----------
def _sales(first, last):
    start, end = _bounds(first, last)
    return (Sale.objects.filter(device_timestamp__gte=start, device_timestamp__lt=end)
            .prefetch_related("adjustments", Prefetch("order__items", queryset=OrderItem.objects.select_related("dish")
                                                      .prefetch_related("adjustments"))))


def _is_cancelled(sale):
    return any(a.kind == AdjustmentKind.CANCELLATION for a in sale.adjustments.all())


def _net(sale):
    """What the sale finally charged and the method the close attributes it to (rule 11)."""
    reverted = sum((a.amount for a in sale.adjustments.all()), ZERO)
    corrections = sorted((a for a in sale.adjustments.all() if a.reason == AdjustmentReason.PAYMENT_CORRECTION),
                         key=lambda a: (a.created_at, a.pk))
    method = corrections[-1].new_payment_method if corrections else sale.payment_method
    return sale.charged_total - reverted, method


def _net_units(item):
    reverted = sum(a.quantity for a in item.adjustments.all()
                   if a.kind == AdjustmentKind.ADJUSTMENT and a.reason != AdjustmentReason.PAYMENT_CORRECTION)
    return item.quantity - reverted


def _buckets(first, last):
    """Chart buckets: hours of the day for one day, weekdays for a week, weeks for a month."""
    days = (last - first).days + 1
    if days == 1:
        return "hora"
    if days <= 7:
        return "dia"
    return "semana"


def sales_by_period(first, last):
    """
    Sales between two dates (both included):
    {total, cash, transfer, tickets, average, cancelled, chart: [(label, amount)]}. tickets does not count cancelled
    sales; the chart has an hour (07 h…), weekday (L…D) or week (S1…S5) per bar.
    """
    totals = {PaymentMethod.CASH: ZERO, PaymentMethod.TRANSFER: ZERO}
    tickets = cancelled = 0
    kind = _buckets(first, last)
    chart = defaultdict(lambda: ZERO)
    for sale in _sales(first, last):
        amount, method = _net(sale)
        totals[method] += amount
        if _is_cancelled(sale):
            cancelled += 1
        else:
            tickets += 1
        when = timezone.localtime(sale.device_timestamp)
        chart[when.hour if kind == "hora" else when.date() if kind == "dia" else (when.day - 1) // 7 + 1] += amount
    total = totals[PaymentMethod.CASH] + totals[PaymentMethod.TRANSFER]
    if kind == "hora":
        bars = [(f"{hour:02d}", chart[hour]) for hour in sorted(chart)]
    elif kind == "dia":
        days = [first + timedelta(days=offset) for offset in range((last - first).days + 1)]
        bars = [(WEEKDAYS[day.weekday()], chart[day]) for day in days]
    else:
        bars = [(f"S{week}", chart[week]) for week in range(1, (last.day - 1) // 7 + 2)]
    return {"total": total, "cash": totals[PaymentMethod.CASH], "transfer": totals[PaymentMethod.TRANSFER],
            "tickets": tickets, "cancelled": cancelled,
            "average": (total / tickets).quantize(Decimal("0.01")) if tickets else ZERO, "chart": bars}


def top_dishes(first, last, limit=6):
    """Best sellers by units, without cancelled sales or reverted units: [{dish_id, name, units}]."""
    units, names = defaultdict(int), {}
    for sale in _sales(first, last):
        if _is_cancelled(sale):
            continue
        for item in sale.order.items.all():
            units[item.dish_id] += _net_units(item)
            names[item.dish_id] = item.dish.name
    ranking = sorted(((d, names[d], u) for d, u in units.items() if u > 0), key=lambda r: (-r[2], r[1]))
    return [{"dish_id": d, "name": n, "units": u} for d, n, u in ranking[:limit]]


# ---------- Inventario ----------
def _movements(first, last, **filters):
    start, end = _bounds(first, last)
    movements = StockMovement.objects.filter(created_at__gte=start, created_at__lt=end, **filters)
    return movements.select_related("ingredient")


def ingredients_used(first, last, limit=7):
    """
    What the sales consumed, net of what cancellations and adjustments gave back, valued at each ingredient's
    current cost: {"items": [{name, unit, quantity, cost}] (the most expensive first), "cost": Decimal}.
    """
    used = defaultdict(Decimal)
    ingredients = {}
    for movement in _movements(first, last, sale_uuid__isnull=False,
                               kind__in=[MovementKind.SALE, MovementKind.ADJUSTMENT]):
        used[movement.ingredient_id] -= movement.quantity
        ingredients[movement.ingredient_id] = movement.ingredient
    items = [{"name": ingredients[pk].name, "unit": ingredients[pk].unit, "quantity": quantity,
              "cost": (quantity * ingredients[pk].unit_cost).quantize(Decimal("0.01"))}
             for pk, quantity in used.items() if quantity > 0]
    items.sort(key=lambda i: (-i["cost"], i["name"]))
    return {"items": items[:limit], "cost": sum((i["cost"] for i in items), ZERO)}


def waste_by_period(first, last):
    """Waste valued at current cost: {"items": [{name, reason, cost}] (most expensive first), "cost", "count"}."""
    items = [{"name": m.ingredient.name, "reason": m.note,
              "cost": (-m.quantity * m.ingredient.unit_cost).quantize(Decimal("0.01"))}
             for m in _movements(first, last, kind=MovementKind.WASTE)]
    items.sort(key=lambda i: (-i["cost"], i["name"]))
    return {"items": items, "cost": sum((i["cost"] for i in items), ZERO), "count": len(items)}


def profit(first, last):
    """Sales minus the cost of the ingredients their recipes used: {sales, cost, amount, margin (0–100 or None)}."""
    sales = sales_by_period(first, last)["total"]
    cost = ingredients_used(first, last, limit=None)["cost"]
    margin = round((sales - cost) / sales * 100) if sales else None
    return {"sales": sales, "cost": cost, "amount": sales - cost, "margin": margin}


# ---------- Corte de caja ----------
def cash_close(session):
    """
    The cash close of a session from what was recorded (rule 5): {session, opening_amount, cash, transfer, total,
    expected_amount, tickets, cancelled, closing_amount, cash_difference, is_open}. While open, closing_amount and
    cash_difference are None; closing is pos.services_cash_session.close_session, which refuses with unsynced sales.
    """
    totals = sales_totals(session)
    sales = list(Sale.objects.filter(cash_session=session).prefetch_related("adjustments"))
    cancelled = sum(1 for sale in sales if _is_cancelled(sale))
    is_open = session.status == SessionStatus.OPEN
    return {
        "session": session, "opening_amount": session.opening_amount,
        "cash": totals["cash"], "transfer": totals["transfer"], "total": totals["cash"] + totals["transfer"],
        "expected_amount": expected_cash(session) if is_open else session.expected_amount,
        "tickets": len(sales) - cancelled, "cancelled": cancelled,
        "closing_amount": session.closing_amount, "cash_difference": session.cash_difference, "is_open": is_open,
    }


# ---------- PDF ----------
def _money(amount):
    return f"${amount:,.2f}"


def daily_sales(day):
    """Rows of the day's sales for the PDF: [{time, ticket, items, method, total, status}], oldest first."""
    rows = []
    for sale in sorted(_sales(day, day), key=lambda s: s.device_timestamp):
        amount, method = _net(sale)
        items = ", ".join(f"{_net_units(i) if not _is_cancelled(sale) else i.quantity}× {i.dish.name}"
                          for i in sale.order.items.all())
        status = "Cancelada" if _is_cancelled(sale) else "Ajustada" if sale.adjustments.all() else ""
        rows.append({"time": timezone.localtime(sale.device_timestamp).strftime("%H:%M"), "ticket": str(sale.uuid)[:8],
                     "items": items, "method": PaymentMethod(method).label, "total": amount, "status": status})
    return rows


def export_daily_sales_pdf(day):
    """The day's sales as a PDF (bytes): a header, the totals by method and a table with one row per sale."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    summary = sales_by_period(day, day)
    rows = daily_sales(day)
    styles = getSampleStyleSheet()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"Ventas del {day:%d/%m/%Y}",
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    story = [
        Paragraph("El Pardo · Ventas del día", styles["Title"]),
        Paragraph(f"{day:%d/%m/%Y}", styles["Heading2"]),
        Paragraph(f"Total: {_money(summary['total'])} · Efectivo: {_money(summary['cash'])} · "
                  f"Transferencia: {_money(summary['transfer'])} · Tickets: {summary['tickets']} · "
                  f"Canceladas: {summary['cancelled']}", styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]
    if rows:
        cell = styles["BodyText"]
        data = [["Hora", "Ticket", "Platillos", "Método", "Total", "Estado"]] + [
            [r["time"], r["ticket"], Paragraph(r["items"], cell), r["method"], _money(r["total"]), r["status"]]
            for r in rows]
        table = Table(data, colWidths=[1.5 * cm, 2 * cm, 7.5 * cm, 2.6 * cm, 2.2 * cm, 2.2 * cm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (4, 1), (4, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("Sin ventas para este día.", styles["Normal"]))
    doc.build(story)
    return buffer.getvalue()
