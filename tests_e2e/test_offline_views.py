"""Productos, Inventario, Caja y Reportes sin red, solo consulta (CLAUDE.md §5-bis; DEC-28, DEC-32)."""
from decimal import Decimal

from apps.pos import services as sales
from apps.pos import services_cash_session as cash

from .base import E2ETestCase


class OfflineScreensTests(E2ETestCase):
    def setUp(self):
        super().setUp()
        cash.open_session(self.admin, Decimal("500.00"))
        pedido = {"lineas": [{"platillo_id": self.burrito.pk, "precio_base_centavos": 7500, "cantidad": 1}]}
        sales.confirm_sale(self.cashier, pedido, "efectivo", 7500)

    def saved(self, path):
        """Waits until the service worker keeps a copy of the screen (the page asks for it with the padlock open)."""
        script = ("(path) => caches.keys().then((names) => Promise.all(names.filter((n) => n.startsWith('sgft-paginas-'))"
                  ".map((n) => caches.open(n).then((cache) => cache.match(path))))).then((found) => found.some(Boolean))")
        self.wait_for(lambda: self.page.evaluate(script, path), f"No se guardó la copia de {path}.")

    def open_caja_with_network(self):
        page = self.page
        self.activate_device()
        self.wait_for_service_worker()
        page.goto(self.url("/reports/cash/"))
        self.unlock()
        page.wait_for_url("**/reports/cash/")
        page.locator("#cash-title").wait_for()
        for path in ("/reports/cash/", "/reports/", "/inventory/", "/catalog/"):
            self.saved(path)

    def test_padlock_screens_open_without_network_after_the_pin(self):
        page = self.page
        self.open_caja_with_network()
        self.context.set_offline(True)

        # The copy of Reportes asks for the PIN, checked on the device against the downloaded verifier.
        page.goto(self.url("/reports/"))
        gate = page.locator('form[aria-labelledby="offline-pin-title"]')
        gate.wait_for()
        self.type_pin(gate, "000000")
        gate.locator("button[type=submit]").click()
        gate.get_by_text("PIN incorrecto").wait_for()
        self.type_pin(gate)
        gate.locator("button[type=submit]").click()
        gate.wait_for(state="detached")
        page.locator("#reports-title").wait_for()
        notice = page.get_by_role("status").filter(has_text="Sin conexión")
        notice.get_by_text("Última sincronización").wait_for()
        notice.get_by_text("Desbloqueado por Alejandro").wait_for()

        # Unlocked for 30 minutes: the other padlock screens open at once, with the figures of their last load.
        page.goto(self.url("/reports/cash/"))
        page.locator("#cash-title").wait_for()
        self.assertEqual(page.locator('form[aria-labelledby="offline-pin-title"]').count(), 0)
        page.get_by_text("$75.00").first.wait_for()
        page.goto(self.url("/inventory/"))
        page.locator("#inventory-title").wait_for()
        page.get_by_text("Tortilla").first.wait_for()

        # An action that needs the server says so instead of failing silently.
        page.get_by_role("button", name="Agregar insumo").click()
        page.get_by_text("esta acción necesita red").wait_for()

    def lock_on_the_server(self):
        """The 30 minutes of the server's padlock are over: the menu shows the padlock modules as PIN buttons."""
        from django.contrib.sessions.backends.db import SessionStore

        from apps.core.mixins import UNLOCKED_BY_KEY, UNLOCKED_UNTIL_KEY
        [key] = [c["value"] for c in self.context.cookies() if c["name"] == "sessionid"]
        session = SessionStore(session_key=key)
        session.pop(UNLOCKED_UNTIL_KEY, None)
        session.pop(UNLOCKED_BY_KEY, None)
        session.save()

    def test_locked_menu_item_goes_to_the_copy_without_network(self):
        page = self.page
        self.open_caja_with_network()
        self.lock_on_the_server()
        page.goto(self.url("/pos/"))
        page.locator('button[data-sgft-url="/reports/cash/"]').wait_for(state="attached")
        self.context.set_offline(True)
        page.reload()
        page.locator("#offline-sale").wait_for()

        # With network the button would open the server's PIN dialog; without it, it goes to the saved copy.
        page.get_by_role("button", name="Abrir menú").click()
        page.locator('#app-menu button[data-sgft-url="/reports/cash/"]').click()
        page.wait_for_url("**/reports/cash/")
        gate = page.locator('form[aria-labelledby="offline-pin-title"]')
        self.type_pin(gate)
        gate.locator("button[type=submit]").click()
        gate.wait_for(state="detached")
        page.locator("#cash-title").wait_for()

    def test_a_screen_never_opened_with_network_explains_what_to_do(self):
        page = self.page
        self.activate_device()
        self.wait_for_service_worker()
        self.context.set_offline(True)
        page.goto(self.url("/inventory/"))
        page.get_by_text("todavía no está guardada en el dispositivo").wait_for()
        page.get_by_role("link", name="Ir a Nueva venta").click()
        page.locator("#offline-sale").wait_for()
