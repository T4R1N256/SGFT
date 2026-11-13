"""
Base of the end-to-end tests: a live server, one Chromium per test class and the data every flow needs.

Each test gets a fresh browser context (cookies, IndexedDB and service worker of its own) and a device activated
the way the food truck does it: the Activar este dispositivo page with an Administrator's PIN (DEC-34).
"""
import os
import time
import unittest
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings

from apps.catalog.models import Category, Dish, Ingredient, Recipe, Units
from apps.pos.models import Modifier, ModifierKind

ENABLED = os.environ.get("SGFT_E2E") == "1"
ADMIN_PIN = "482913"
TIMEOUT = 15_000  # ms; the service worker's first install downloads Workbox, Dexie, htmx and Alpine

if ENABLED:
    # Playwright's sync API runs an event loop in this thread; Django's ORM is still called synchronously.
    os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@unittest.skipUnless(ENABLED, "Pruebas E2E: corre con SGFT_E2E=1 y Playwright instalado (ver tests_e2e/__init__.py).")
@override_settings(SGFT_PIN_VERIFIER_ITERATIONS=1000)
class E2ETestCase(StaticLiveServerTestCase):
    host = "localhost"  # service workers need a secure context: localhost counts as one

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from playwright.sync_api import sync_playwright
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()
        if connection.vendor == "postgresql":
            # The live server's threads may leave connections open, and PostgreSQL refuses to drop the test
            # database while someone is connected.
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                               "WHERE datname = current_database() AND pid <> pg_backend_pid()")

    def setUp(self):
        users = get_user_model().objects
        self.admin = users.create_user(username="dueno", password=ADMIN_PIN, role="admin", first_name="Alejandro")
        self.cashier = users.create_user(username="caja", password="x-9Lq!pr3", role="cashier")
        category = Category.objects.create(name="Burritos", emoji="🌯")
        self.tortilla = Ingredient.objects.create(name="Tortilla", unit=Units.PIECE, stock=Decimal("50"),
                                                  min_stock=Decimal("5"))
        self.cheese = Ingredient.objects.create(name="Queso", unit=Units.KG, stock=Decimal("3"),
                                                min_stock=Decimal("0.5"))
        self.burrito = Dish.objects.create(name="Burrito de asada", category=category, price=Decimal("75.00"))
        Recipe.objects.create(dish=self.burrito, ingredient=self.tortilla, quantity=Decimal("1"))
        Modifier.objects.create(dish=self.burrito, ingredient=self.cheese, kind=ModifierKind.ADD,
                                price_adjustment=Decimal("15.00"), quantity=Decimal("0.030"))
        self.context = self.browser.new_context(locale="es-MX")
        self.context.set_default_timeout(TIMEOUT)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.addCleanup(self.context.close)

    def tearDown(self):
        self.assertEqual(self.errors, [], "La página lanzó errores de JavaScript.")

    # ----- Helpers -----
    def url(self, path):
        return f"{self.live_server_url}{path}"

    def type_pin(self, form, pin=ADMIN_PIN):
        boxes = form.locator("input[name=pin]")
        for index, digit in enumerate(pin):
            boxes.nth(index).fill(digit)

    def activate_device(self):
        """Activar este dispositivo with the Administrator's PIN: the device keeps the cashier's session."""
        self.page.goto(self.url("/accounts/activate/"))
        form = self.page.locator("#dialog form")
        self.type_pin(form)
        form.locator("button[type=submit]").click()
        self.page.wait_for_url("**/pos/")

    def unlock(self, pin=ADMIN_PIN):
        """Answers the «PIN de administrador» dialog of a module with a padlock."""
        form = self.page.locator("#dialog form", has_text="PIN de administrador")
        self.type_pin(form, pin)
        form.locator("button[type=submit]").click()

    def wait_for_service_worker(self):
        """The first visit installs the service worker; offline flows need it controlling the page."""
        self.page.wait_for_function(
            "navigator.serviceWorker.getRegistration('/').then((r) => Boolean(r && r.active))", timeout=60_000)
        self.page.reload()
        self.page.wait_for_function("navigator.serviceWorker.controller !== null")
        self.page.wait_for_function("Boolean(window.sgftDb)")

    def pending(self):
        """«N pendientes» of the menu: operations queued on the device."""
        return int(self.page.locator("[data-sgft-pendientes]").first.inner_text().strip())

    def wait_for(self, condition, message):
        """Polls a database condition: what the live server saved is committed, so this thread sees it."""
        deadline = time.monotonic() + TIMEOUT / 1000
        while not condition():
            if time.monotonic() > deadline:
                self.fail(message)
            self.page.wait_for_timeout(100)

    def go_offline(self):
        """Cuts the network and reloads: the service worker serves Nueva venta and ventaSinRed takes over."""
        self.context.set_offline(True)
        self.page.reload()
        self.page.locator("#offline-sale").wait_for()

    def sell_offline(self, units=1):
        """Queues a sale on the device with the catalog of the last load."""
        offline = self.page.locator("#offline-sale")
        card = offline.locator(".sgft-dish-card", has_text="Burrito de asada")
        for _ in range(units):
            card.click()
        offline.get_by_role("button", name="Confirmar compra").click()
        self.page.get_by_text("Venta guardada en el dispositivo").wait_for()

    def reconnect(self):
        """Brings the network back: offline.js sends the queue and reloads the page with the server's state."""
        with self.page.expect_navigation():
            self.context.set_offline(False)
        self.page.wait_for_function(
            "document.querySelector('[data-sgft-pendientes]').textContent.trim() === '0'")

    def sync(self):
        """What «Sincronizar» of the menu does, without reloading; returns whether the server answered."""
        return self.page.evaluate("window.sgftSinRed.sincronizar().then((resultado) => resultado.ok)")
