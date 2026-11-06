"""Tests of apps.core: role and admin PIN decorators (WBS 3.1.3) and the shell context processor."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import timezone
from django.views import View

from apps.core import mixins
from apps.core.context_processors import shell


def _ok(request):
    return HttpResponse("ok")


FAST = {"PASSWORD_HASHERS": ["django.contrib.auth.hashers.MD5PasswordHasher"], "SGFT_PIN_VERIFIER_ITERATIONS": 1000}


@override_settings(**FAST)
class AccessBase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user("admin1", password="482915", role="admin")
        self.cashier = User.objects.create_user("caja1", password="482915", role="cashier")
        self.factory = RequestFactory()

    def request(self, user=None, htmx=False, path="/inventory/"):
        request = self.factory.get(path, HTTP_HX_REQUEST="true" if htmx else None) if htmx \
            else self.factory.get(path)
        SessionMiddleware(lambda r: None).process_request(request)
        request.user = user or AnonymousUser()
        request.htmx = htmx
        return request


class UnlockTests(AccessBase):
    def test_unlock_lasts_thirty_minutes(self):
        request = self.request(self.cashier)
        mixins.unlock_admin(request, self.admin)
        self.assertEqual(mixins.unlocked_admin(request), self.admin)
        request.session[mixins.UNLOCKED_UNTIL_KEY] = (timezone.now() - timedelta(seconds=1)).timestamp()
        self.assertIsNone(mixins.unlocked_admin(request))

    def test_unlock_by_deactivated_or_demoted_admin_does_not_count(self):
        request = self.request(self.cashier)
        mixins.unlock_admin(request, self.admin)
        self.admin.role = "cashier"
        self.admin.save()
        self.assertFalse(mixins.is_admin_unlocked(request))

    def test_lock_admin_closes_the_padlock(self):
        request = self.request(self.cashier)
        mixins.unlock_admin(request, self.admin)
        mixins.lock_admin(request)
        self.assertFalse(mixins.is_admin_unlocked(request))


@override_settings(LOGIN_URL="/activar/")
class RoleRequiredTests(AccessBase):
    def test_without_session_redirects_to_activation(self):
        response = mixins.role_required()(_ok)(self.request())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/activar/?next="))

    def test_without_session_htmx_gets_401_and_hx_redirect(self):
        response = mixins.role_required()(_ok)(self.request(htmx=True))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["HX-Redirect"], "/activar/")

    def test_cashier_and_admin_pass_by_default(self):
        for user in (self.cashier, self.admin):
            self.assertEqual(mixins.role_required()(_ok)(self.request(user)).status_code, 200)

    def test_cashier_is_rejected_from_admin_only_view(self):
        response = mixins.role_required("admin")(_ok)(self.request(self.cashier, htmx=True))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["HX-Retarget"], "#messages")
        self.assertContains(response, "no tiene permiso", status_code=403)

    def test_inactive_user_is_rejected(self):
        self.cashier.is_active = False
        response = mixins.role_required()(_ok)(self.request(self.cashier))
        self.assertEqual(response.status_code, 403)


@override_settings(LOGIN_URL="/activar/")
class AdminPinRequiredTests(AccessBase):
    view = staticmethod(mixins.admin_pin_required("Inventario")(_ok))

    def test_locked_full_page_shows_pin_required_with_dialog(self):
        response = self.view(self.request(self.cashier))
        self.assertEqual(response.status_code, 403)
        html = response.content.decode()
        self.assertIn("Inventario requiere PIN", html)
        self.assertIn(reverse("accounts:admin_pin"), html)

    def test_locked_htmx_gets_dialog_in_dialog_target(self):
        response = self.view(self.request(self.cashier, htmx=True))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["HX-Retarget"], "#dialog")

    def test_unlocked_passes(self):
        request = self.request(self.cashier)
        mixins.unlock_admin(request, self.admin)
        self.assertEqual(self.view(request).status_code, 200)

    def test_without_session_goes_to_activation_first(self):
        self.assertEqual(self.view(self.request()).status_code, 302)

    def test_falls_back_to_admin_login_while_activation_url_is_missing(self):
        with self.settings(LOGIN_URL="accounts:no_such_view"):
            response = self.view(self.request())
        self.assertTrue(response["Location"].startswith(reverse("admin:login")))


class ClassMixinTests(AccessBase):
    def test_role_required_mixin(self):
        class AdminOnly(mixins.RoleRequiredMixin, View):
            allowed_roles = ("admin",)

            def get(self, request):
                return HttpResponse("ok")

        self.assertEqual(AdminOnly.as_view()(self.request(self.admin)).status_code, 200)
        self.assertEqual(AdminOnly.as_view()(self.request(self.cashier)).status_code, 403)

    def test_admin_pin_required_mixin(self):
        class Locked(mixins.AdminPinRequiredMixin, View):
            module_label = "Caja"

            def get(self, request):
                return HttpResponse("ok")

        self.assertEqual(Locked.as_view()(self.request(self.cashier)).status_code, 403)


class ShellContextTests(AccessBase):
    def test_locked_menu_sends_padlock_modules_to_the_pin_dialog(self):
        context = shell(self.request(self.cashier))
        modules = {m["key"]: m for m in context["nav_modules"]}
        self.assertEqual(modules["pos"]["pin_url"], "")
        self.assertIn(reverse("accounts:admin_pin"), modules["inventory"]["pin_url"])
        self.assertFalse(context["admin_unlocked"])

    def test_unlocked_menu_navigates_directly(self):
        request = self.request(self.cashier)
        mixins.unlock_admin(request, self.admin)
        context = shell(request)
        self.assertTrue(all(m["pin_url"] == "" for m in context["nav_modules"]))
        self.assertTrue(context["admin_unlocked"])

    def test_every_page_gets_the_shell(self):
        self.client.force_login(self.cashier)
        response = self.client.get(reverse("reports:cash"))
        self.assertIn("admin_unlocked", response.context)

    def test_active_module_follows_the_url(self):
        for name, key in (("pos:order_builder", "pos"), ("catalog:dish_catalog", "products"),
                          ("inventory:ingredient_list", "inventory"), ("reports:cash", "cash"),
                          ("reports:reports", "reports")):
            request = self.request(self.cashier, path=reverse(name))
            request.resolver_match = resolve(reverse(name))
            self.assertEqual(shell(request)["active_module"], key, name)

    def test_user_initials(self):
        self.cashier.first_name, self.cashier.last_name = "Carla", "Mora"
        self.assertEqual(shell(self.request(self.cashier))["user_initials"], "CM")
        self.assertEqual(shell(self.request())["user_initials"], "")
