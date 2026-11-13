"""
Cash state of the top bar on every page (WBS 3.5.1, rule 12): whether a session is open and what it has charged.
It lives in pos because the session is a pos model; catalog and inventory show it without importing pos, and core
stays free of other apps. A view that passes cash_session_open or session_total overrides these values (Nueva
venta does, after opening the till or charging a sale).
"""
from decimal import Decimal

from apps.pos.services_cash_session import current_session, sales_totals


def cash_session(request):
    session = current_session()
    if session is None:
        return {"cash_session_open": False, "session_total": None}
    return {"cash_session_open": True, "session_total": sum(sales_totals(session).values(), Decimal("0.00"))}
