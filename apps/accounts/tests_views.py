"""View tests and view–template contract for apps.accounts (WBS 3.1.2). Author: Yahir."""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.core.mixins import unlocked_admin

ADMIN_PIN = "482915"
HTMX = {"HTTP_HX_REQUEST": "true"}


def pin(digits):
    return {"pin": list(digits)}


class AccessViewsBase(TestCase):
    def setUp(self):
        cache.clear()  # the attempt counter lives in the cache, shared by every test
        users = get_user_model().objects
        self.admin = users.create_user(username="dueno", password=ADMIN_PIN, role="admin")
        self.cashier = users.create_user(username="caja", password="731406", role="cashier")
        self.activate_url = reverse("accounts:activate_device")
        self.sales_url = reverse("pos:order_builder")

    def tearDown(self):
        cache.clear()


class ActivateDeviceViewTests(AccessViewsBase):
    def test_page_has_no_menu_nor_top_bar(self):
        response = self.client.get(self.activate_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/activate_device.html")
        self.assertNotContains(response, "sidebar-waves.svg")  # components/sidebar.html
        self.assertNotContains(response, 'type="search"')  # components/top_bar.html

    def test_page_says_what_to_do_with_the_dialog_open(self):
        response = self.client.get(self.activate_url)
        self.assertContains(response, "Activar este dispositivo")
        self.assertContains(response, "Un administrador debe escribir su PIN.")
        self.assertTemplateUsed(response, "accounts/partials/activate_dialog.html")
        self.assertEqual(response.content.decode().count('name="pin"'), 6)

    def test_htmx_get_returns_only_the_dialog(self):
        response = self.client.get(self.activate_url, **HTMX)
        self.assertTemplateUsed(response, "accounts/partials/activate_dialog.html")
        self.assertTemplateNotUsed(response, "accounts/activate_device.html")
        self.assertContains(response, f'hx-post="{self.activate_url}"')

    def test_admin_pin_signs_the_device_in_as_the_cashier(self):
        response = self.client.post(self.activate_url, pin(ADMIN_PIN), **HTMX)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["HX-Redirect"], self.sales_url)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.cashier.pk)

    def test_without_htmx_it_redirects(self):
        response = self.client.post(self.activate_url, pin(ADMIN_PIN))
        self.assertRedirects(response, self.sales_url, fetch_redirect_response=False)

    def test_goes_back_to_next_but_never_to_another_site(self):
        response = self.client.post(self.activate_url, {**pin(ADMIN_PIN), "next": "/inventory/"}, **HTMX)
        self.assertEqual(response["HX-Redirect"], "/inventory/")
        self.client.logout()
        response = self.client.post(self.activate_url, {**pin(ADMIN_PIN), "next": "https://malo.example/"}, **HTMX)
        self.assertEqual(response["HX-Redirect"], self.sales_url)

    def test_wrong_pin_is_422_in_the_dialog(self):
        response = self.client.post(self.activate_url, pin("000000"), **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response["HX-Retarget"], "#dialog")
        self.assertContains(response, "PIN incorrecto.", status_code=422)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_cashier_password_does_not_activate(self):
        response = self.client.post(self.activate_url, pin("731406"), **HTMX)
        self.assertContains(response, "PIN incorrecto.", status_code=422)

    def test_incomplete_pin_does_not_count_as_an_attempt(self):
        for _ in range(6):
            response = self.client.post(self.activate_url, pin("12a"), **HTMX)
            self.assertContains(response, "Escribe los 6 dígitos del PIN.", status_code=422)
        self.assertEqual(self.client.post(self.activate_url, pin(ADMIN_PIN), **HTMX).status_code, 204)

    def test_five_failures_lock_even_with_a_new_cookie(self):
        for _ in range(5):
            self.client.post(self.activate_url, pin("000000"), **HTMX)
        self.client.cookies.clear()  # deleting the cookie does not reset the limit: it lives in the cache
        response = self.client.post(self.activate_url, pin(ADMIN_PIN), **HTMX)
        self.assertContains(response, "Demasiados intentos. Intenta de nuevo en 15 min.", status_code=422)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_without_an_active_cashier(self):
        self.cashier.is_active = False
        self.cashier.save()
        response = self.client.post(self.activate_url, pin(ADMIN_PIN), **HTMX)
        self.assertContains(response, "No hay una cuenta de cajero activa. Pide al administrador que la cree en "
                                      "Django Admin.", status_code=422)

    def test_activated_device_goes_straight_to_sales(self):
        self.client.force_login(self.cashier)
        self.assertRedirects(self.client.get(self.activate_url), self.sales_url, fetch_redirect_response=False)
        self.assertEqual(self.client.post(self.activate_url, pin(ADMIN_PIN), **HTMX).status_code, 409)

class AdminPinViewTests(AccessViewsBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.cashier)  # the device is already activated
        self.pin_url = reverse("accounts:admin_pin") + "?module=Inventario"

    def test_get_returns_the_dialog(self):
        response = self.client.get(self.pin_url + "&next=/inventory/", **HTMX)
        self.assertTemplateUsed(response, "components/pin_dialog.html")
        self.assertContains(response, "Para entrar a Inventario")
        self.assertContains(response, 'value="/inventory/"')

    def test_needs_an_activated_device(self):
        self.client.logout()
        response = self.client.get(self.pin_url, **HTMX)
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response["HX-Redirect"].startswith(self.activate_url))

    def test_admin_pin_unlocks_in_their_name(self):
        response = self.client.post(self.pin_url, {**pin(ADMIN_PIN), "next": "/inventory/"}, **HTMX)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["HX-Redirect"], "/inventory/")
        request = type("Request", (), {"session": self.client.session})()
        self.assertEqual(unlocked_admin(request), self.admin)

    def test_any_six_digits_no_longer_unlock(self):
        response = self.client.post(self.pin_url, {**pin("123456"), "next": "/inventory/"}, **HTMX)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response["HX-Retarget"], "#dialog")
        self.assertContains(response, "PIN incorrecto.", status_code=422)
        self.assertContains(response, "Para entrar a Inventario", status_code=422)

    def test_incomplete_pin(self):
        response = self.client.post(self.pin_url, pin("12"), **HTMX)
        self.assertContains(response, "Escribe los 6 dígitos del PIN.", status_code=422)

    def test_padlocked_screen_opens_only_after_the_real_pin(self):
        inventory = reverse("inventory:ingredient_list")
        self.assertEqual(self.client.get(inventory).status_code, 403)
        self.client.post(self.pin_url, {**pin(ADMIN_PIN), "next": inventory}, **HTMX)
        self.assertEqual(self.client.get(inventory).status_code, 200)
