"""Cierre de caja desde Caja (WBS 4.6, 3.5.7; reglas 5 y 13)."""
import re
from decimal import Decimal

from apps.pos import services as sales
from apps.pos import services_cash_session as cash
from apps.pos.models import SessionStatus

from .base import E2ETestCase


class CashCloseTests(E2ETestCase):
    def setUp(self):
        super().setUp()
        self.session = cash.open_session(self.admin, Decimal("500.00"))
        pedido = {"lineas": [{"platillo_id": self.burrito.pk, "precio_base_centavos": 7500, "cantidad": 1}]}
        sales.confirm_sale(self.cashier, pedido, "efectivo", 7500)

    def open_close_dialog(self, locked=True):
        page = self.page
        page.goto(self.url("/reports/cash/"))
        if locked:
            self.unlock()  # Caja has a padlock (DEC-32); it stays open 30 minutes
        page.wait_for_url("**/reports/cash/")
        page.get_by_role("button", name="Cerrar caja").click()
        return page.locator("#dialog form")

    def session_status(self):
        self.session.refresh_from_db()
        return self.session.status

    def test_close_records_the_cash_difference_without_blocking(self):
        self.activate_device()
        dialog = self.open_close_dialog()
        dialog.get_by_text("$575.00").wait_for()  # opening $500 + cash sales $75
        dialog.locator("input[name=closing_amount]").fill("570")
        dialog.get_by_role("button", name="Cerrar caja").click()

        self.page.wait_for_url("**/pos/")
        self.page.get_by_text("Caja cerrada, diferencia de").wait_for()
        self.assertEqual(self.session_status(), SessionStatus.CLOSED)
        self.assertEqual((self.session.closed_by, self.session.expected_amount, self.session.cash_difference),
                         (self.admin, Decimal("575.00"), Decimal("-5.00")))

    def test_close_is_refused_while_the_device_has_pending_sales(self):
        self.activate_device()
        self.wait_for_service_worker()
        self.go_offline()
        self.sell_offline()

        # The network is back but the server cannot be reached for /pos/sync/: the sale stays queued.
        self.context.route("**/pos/sync/", lambda route: route.abort())
        self.context.set_offline(False)
        dialog = self.open_close_dialog()
        dialog.get_by_text(re.compile(r"^\s*1 operaci.n pendiente")).wait_for()  # X-Pendientes from the device
        dialog.locator("input[name=closing_amount]").fill("650")
        dialog.get_by_role("button", name="Cerrar caja").click()
        self.page.locator("#dialog").get_by_text("faltan 1 venta por sincronizar").wait_for()
        self.assertEqual(self.session_status(), SessionStatus.OPEN)

        # Once synced, the same close goes through and counts the offline sale.
        self.context.unroute("**/pos/sync/")
        self.assertTrue(self.sync())
        dialog = self.open_close_dialog(locked=False)
        dialog.get_by_text("$650.00").wait_for()
        dialog.locator("input[name=closing_amount]").fill("650")
        dialog.get_by_role("button", name="Cerrar caja").click()
        self.page.wait_for_url("**/pos/")
        self.assertEqual(self.session_status(), SessionStatus.CLOSED)
        self.assertEqual(self.session.cash_difference, Decimal("0.00"))
