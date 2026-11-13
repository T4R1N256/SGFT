"""Nueva venta con y sin red (WBS 3.4.8; reglas 1, 2, 7, 8 y 12)."""
import re
from decimal import Decimal

from apps.pos import services_cash_session as cash
from apps.pos.models import Sale

from .base import E2ETestCase


class SaleWithNetworkTests(E2ETestCase):
    def test_open_the_till_sell_with_an_extra_and_charge_by_transfer(self):
        page = self.page
        self.activate_device()
        page.get_by_text("La caja está cerrada").first.wait_for()

        # Only an Administrator opens the till (rule 13): the padlock asks for the PIN first.
        page.get_by_role("button", name="Abrir caja").first.click()
        self.unlock()
        dialog = page.locator("form[aria-labelledby=open-cash-title]")
        dialog.locator("input[name=opening_amount]").fill("500")
        dialog.locator("button[type=submit]").click()

        card = page.get_by_role("button", name=re.compile("^Agregar Burrito de asada"))
        card.click()
        page.get_by_role("button", name=re.compile("En el ticket: 1")).wait_for()
        card.click()
        page.get_by_role("button", name=re.compile("En el ticket: 2")).wait_for()
        page.get_by_role("button", name="Personalizar Burrito de asada").click()
        page.locator("#dialog").get_by_label(re.compile("queso", re.IGNORECASE)).check()
        page.locator("#dialog").get_by_role("button", name="Guardar").click()
        summary = page.locator("#order-summary")
        summary.get_by_text("$180.00").first.wait_for()  # 2 × ($75 + $15 extra), priced by the server
        summary.get_by_role("button", name="Transferencia").click()
        summary.get_by_role("button", name="Confirmar compra").click()

        self.wait_for(Sale.objects.exists, "La venta no llegó al servidor.")
        sale = Sale.objects.get()
        self.assertEqual((sale.charged_total, sale.payment_method, sale.created_by),
                         (Decimal("180.00"), "transfer", self.cashier))
        self.assertEqual((sale.cash_session.opened_by, sale.cash_session.opening_amount),
                         (self.admin, Decimal("500.00")))
        # The inventory is deducted with the sale (rule 1); the extra adds its quantity (rule 2).
        self.tortilla.refresh_from_db()
        self.cheese.refresh_from_db()
        self.assertEqual((self.tortilla.stock, self.cheese.stock), (Decimal("48"), Decimal("2.940")))


class SaleWithoutNetworkTests(E2ETestCase):
    def test_a_sale_without_network_is_queued_and_synced_once(self):
        session = cash.open_session(self.admin, Decimal("500.00"))
        self.activate_device()
        self.wait_for_service_worker()

        self.go_offline()
        self.sell_offline(units=2)
        self.assertEqual(self.pending(), 1)
        self.assertFalse(Sale.objects.exists())  # nothing reaches the server without network

        # The queue survives a reload: it lives in IndexedDB, not in the page.
        self.page.reload()
        self.page.locator("#offline-sale").wait_for()
        self.assertEqual(self.pending(), 1)

        self.reconnect()
        self.wait_for(Sale.objects.exists, "La venta no se sincronizó.")
        sale = Sale.objects.get()
        self.assertEqual((sale.charged_total, sale.cash_session, sale.created_by),
                         (Decimal("150.00"), session, self.cashier))
        self.assertLess(sale.device_timestamp, sale.server_timestamp)
        self.tortilla.refresh_from_db()
        self.assertEqual(self.tortilla.stock, Decimal("48"))  # deducted when it reached the server (rule 1)

        # Syncing again (what «Sincronizar» of the menu does) sends nothing: the UUID was applied once (rule 8).
        self.assertTrue(self.sync())
        self.assertEqual((self.pending(), Sale.objects.count()), (0, 1))
