"""Apertura del turno de caja con y sin red (WBS 3.4.8, 3.5.1; reglas 12 y 13, DEC-27 y DEC-28)."""
from decimal import Decimal

from apps.pos.models import CashRegisterSession, Sale

from .base import E2ETestCase


class OpeningTests(E2ETestCase):
    def test_a_wrong_pin_does_not_open_the_till(self):
        page = self.page
        self.activate_device()
        page.get_by_role("button", name="Abrir caja").first.click()
        self.unlock("111111")
        page.locator("#dialog [aria-invalid=true]").first.wait_for()
        self.assertFalse(CashRegisterSession.objects.exists())

        self.unlock()
        dialog = page.locator("form[aria-labelledby=open-cash-title]")
        dialog.locator("input[name=opening_amount]").fill("350.50")
        dialog.locator("button[type=submit]").click()
        self.wait_for(CashRegisterSession.objects.exists, "La caja no se abrió.")
        session = CashRegisterSession.objects.get()
        self.assertEqual((session.opened_by, session.opening_amount, session.status),
                         (self.admin, Decimal("350.50"), "open"))

    def test_opening_without_network_uses_the_pin_verifier_and_syncs(self):
        page = self.page
        self.activate_device()
        self.wait_for_service_worker()
        self.go_offline()

        # The device checks the PIN against the PBKDF2 verifier it downloaded; the PIN itself never was stored.
        offline = page.locator("#offline-sale")
        offline.get_by_role("button", name="Abrir caja").click()
        form = page.locator('form[aria-labelledby="offline-open-title"]')
        self.type_pin(form, "000000")
        form.locator("input[name=opening_amount]").fill("500")
        form.locator("button[type=submit]").click()
        form.get_by_text("PIN").first.wait_for()
        self.type_pin(form)
        form.locator("button[type=submit]").click()
        page.get_by_text("Caja abierta en el dispositivo").wait_for()
        self.sell_offline()
        self.assertEqual(self.pending(), 2)  # the opening and the sale
        self.assertFalse(CashRegisterSession.objects.exists())

        self.reconnect()
        self.wait_for(Sale.objects.exists, "La apertura y la venta no se sincronizaron.")
        session = CashRegisterSession.objects.get()
        self.assertEqual((session.opened_by, session.opening_amount), (self.admin, Decimal("500.00")))
        self.assertEqual(Sale.objects.get().cash_session, session)  # the sale points to the device's session
