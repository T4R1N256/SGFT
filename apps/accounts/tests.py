"""Unit tests for apps.accounts. Whoever implements a service writes its tests."""
import base64
import hashlib

from django.contrib.admin.sites import site
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.admin import UserAdmin
from apps.accounts.models import DEFAULT_PIN_VERIFIER_ITERATIONS, Role
from apps.accounts.services import (
    MAX_PIN_ATTEMPTS, InvalidPinError, NoCashierAvailableError, PinLockedError, activate_device, change_role,
    create_user, deactivate_user, guard_admin_login, pin_minutes_locked, verify_admin_pin,
)

class UserModelTests(TestCase):
    """WBS 3.1.1 — custom user model with role (author: Jesús)."""

    def test_project_uses_custom_user_model(self):
        self.assertEqual(get_user_model()._meta.label, "accounts.User")

    def test_new_user_defaults_to_cashier(self):
        user = get_user_model().objects.create_user(username="cajero1", password="x-9Lq!pr2")
        self.assertEqual(user.role, Role.CASHIER)

    def test_superuser_gets_admin_role(self):
        admin = get_user_model().objects.create_superuser(username="dueno", password="x-9Lq!pr2")
        self.assertEqual(admin.role, Role.ADMIN)
        self.assertTrue(admin.is_staff)

    def test_password_is_hashed(self):
        user = get_user_model().objects.create_user(username="cajero2", password="x-9Lq!pr2")
        self.assertNotEqual(user.password, "x-9Lq!pr2")
        self.assertTrue(user.check_password("x-9Lq!pr2"))


FAST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=FAST_HASHERS, SGFT_PIN_VERIFIER_ITERATIONS=1000)
class AdminPinTests(TestCase):
    """WBS 3.1.1 — the admin PIN is the 6-digit account password, plus its offline verifier (pin-administrador-sin-red.md)."""

    def create_admin(self, username="dueno", password="482915"):
        return get_user_model().objects.create_user(username=username, password=password, role=Role.ADMIN)

    def test_pin_is_the_password(self):
        admin = self.create_admin()
        self.assertTrue(admin.check_password("482915"))
        self.assertFalse(admin.check_password("482914"))
        self.assertNotIn("482915", admin.password)

    def test_create_user_derives_the_offline_verifier(self):
        admin = self.create_admin()
        admin.refresh_from_db()
        salt = base64.b64decode(admin.pin_verifier_salt)
        expected = hashlib.pbkdf2_hmac("sha256", b"482915", salt, admin.pin_verifier_iterations)
        self.assertEqual(base64.b64decode(admin.pin_verifier), expected)
        self.assertEqual(admin.pin_verifier_iterations, 1000)
        self.assertEqual(len(salt), 16)
        self.assertIsNotNone(admin.pin_changed_at)

    def test_verifier_never_contains_the_pin(self):
        admin = self.create_admin()
        self.assertNotIn("482915", admin.pin_verifier)
        self.assertNotIn("482915", admin.pin_verifier_salt)

    def test_password_that_is_not_six_digits_gets_no_verifier(self):
        for password in ("x-9Lq!pr2", "12345", "1234567", "12a456", "١٢٣٤٥٦"):
            admin = self.create_admin(username=f"u{len(password)}{password[:2]}", password=password)
            self.assertFalse(admin.has_offline_verifier, password)
            self.assertEqual((admin.pin_verifier_salt, admin.pin_verifier_iterations), ("", 0))

    def test_same_pin_gets_a_different_salt_per_user(self):
        one, other = self.create_admin(), self.create_admin(username="socio")
        self.assertNotEqual(one.pin_verifier_salt, other.pin_verifier_salt)
        self.assertNotEqual(one.pin_verifier, other.pin_verifier)

    def test_changing_the_password_replaces_the_verifier(self):
        admin = self.create_admin()
        old = admin.pin_verifier
        admin.set_password("730261")
        self.assertNotEqual(admin.pin_verifier, old)
        self.assertTrue(admin.check_password("730261"))
        admin.set_password("x-9Lq!pr2")
        self.assertFalse(admin.has_offline_verifier)

    def test_unusable_password_clears_the_verifier(self):
        admin = self.create_admin()
        admin.set_unusable_password()
        self.assertFalse(admin.has_offline_verifier)
        self.assertFalse(admin.check_password("482915"))

    def test_production_iterations_follow_the_design(self):
        self.assertEqual(DEFAULT_PIN_VERIFIER_ITERATIONS, 600_000)


# Authentication unit tests by Jared and Diego

User = get_user_model()
PASSWORD = '482915'

class AuthenticationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='cajero1', password = PASSWORD)



    # An inactive employee account cannot log in.
    def test_inactive_user_doesnt_login(self):
        self.user.is_active = False
        self.user.save()
        self.assertIsNone(authenticate(username='cajero1', password=PASSWORD))


class AccessRestrictionTest(TestCase):
    def setUp(self):
        self.cashier=User.objects.create_user(
            username='cajero1',
            password=PASSWORD
        )
        self.admin=User.objects.create_superuser(
            username='root',
            email='root@gmail.com',
            password=PASSWORD
        )

    def test_anonymous_redirected_to_login(self):
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code,302)
        self.assertIn("/admin/login/", resp["Location"])

    def test_cashier_cannot_access_admin(self):
        self.client.force_login(self.cashier)
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code,302)

    def test_admin_can_access_to_admin(self):
        self.client.force_login(self.admin)
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code,200)

    def test_admin_role_can_open_admin(self):
        admin = create_user(username="admin2", password=PASSWORD, role=Role.ADMIN)
        self.client.force_login(admin)
        self.assertEqual(self.client.get("/admin/").status_code, 200)

# Role unit tests by Diego

class RoleTests(TestCase):
    """Role model tests (WBS 3.1.5)."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_test",
            password=PASSWORD,
            role=Role.ADMIN,
        )
        self.cashier = User.objects.create_user(
            username="cashier_test",
            password=PASSWORD,
            role=Role.CASHIER,
        )


    # The is_admin property is True only for ADMIN role.
    def test_is_admin_property(self):
        self.assertTrue(self.admin.is_admin)
        self.assertFalse(self.cashier.is_admin)

    # The is_cashier property is True only for CASHIER role.
    def test_is_cashier_property(self):
        self.assertTrue(self.cashier.is_cashier)
        self.assertFalse(self.admin.is_cashier)




@override_settings(PASSWORD_HASHERS=FAST_HASHERS, SGFT_PIN_VERIFIER_ITERATIONS=1000)
class SixDigitPasswordTests(TestCase):
    """WBS 3.1.1 — the account password is the 6-digit admin PIN."""

    def test_six_digits_are_accepted(self):
        validate_password("482915")

    def test_other_passwords_are_rejected(self):
        for bad in ("48291", "4829150", "48a915", "123456", "x-9Lq!pr2"):
            with self.assertRaises(ValidationError, msg=bad):
                validate_password(bad)

    def test_create_user_accepts_a_six_digit_admin(self):
        admin = create_user("dueno", "482915", Role.ADMIN)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.has_offline_verifier)

    def test_create_user_rejects_a_bad_password(self):
        with self.assertRaises(ValidationError):
            create_user("dueno", "Clave12345", Role.ADMIN)

@override_settings(PASSWORD_HASHERS=FAST_HASHERS, SGFT_PIN_VERIFIER_ITERATIONS=1000)
class ChangeRoleTests(TestCase):
    """WBS 3.1.1 — change_role keeps is_staff in step with the role."""

    def test_syncs_is_staff_both_ways(self):
        user = create_user("ana", "730261", Role.CASHIER)
        self.assertTrue(change_role(user, Role.ADMIN).is_staff)
        self.assertFalse(change_role(user, Role.CASHIER).is_staff)

    def test_superuser_keeps_admin_access(self):
        root = get_user_model().objects.create_superuser("root", password="730261")
        self.assertTrue(change_role(root, Role.CASHIER).is_staff)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS, SGFT_PIN_VERIFIER_ITERATIONS=1000)
class VerifyAdminPinTests(TestCase):
    """WBS 3.1.2 y 4.4 — PIN de Administrador con límite de intentos (autor: Diego)."""

    def setUp(self):
        cache.clear()
        self.admin = create_user("dueno", "482915", role=Role.ADMIN)
        self.cashier = create_user("caja", "730264")

    def test_right_pin_returns_the_admin(self):
        self.assertEqual(verify_admin_pin("482915"), self.admin)

    def test_cashier_pin_is_not_an_admin_pin(self):
        with self.assertRaises(InvalidPinError):
            verify_admin_pin("730264")

    def test_inactive_admin_pin_is_rejected(self):
        create_user("otro", "591736", role=Role.ADMIN)
        self.admin.is_active = False
        self.admin.save()
        with self.assertRaises(InvalidPinError):
            verify_admin_pin("482915")

    def test_malformed_pin_counts_as_a_failure(self):
        for pin in ("", "12345", "abcdef", None):
            with self.assertRaises(InvalidPinError):
                verify_admin_pin(pin)

    def test_five_failures_lock_the_pin_even_for_the_right_one(self):
        for _ in range(MAX_PIN_ATTEMPTS - 1):
            with self.assertRaises(InvalidPinError):
                verify_admin_pin("000001")
        with self.assertRaises(PinLockedError) as locked:
            verify_admin_pin("000001")
        self.assertEqual(locked.exception.minutes_left, 15)
        with self.assertRaises(PinLockedError):
            verify_admin_pin("482915")
        self.assertEqual(pin_minutes_locked(), 15)

    def test_lock_expires(self):
        for _ in range(MAX_PIN_ATTEMPTS):
            with self.assertRaises(InvalidPinError):
                verify_admin_pin("000001")
        cache.set("accounts:pin_locked_until", timezone.now().timestamp() - 1)
        self.assertEqual(verify_admin_pin("482915"), self.admin)

    def test_success_resets_the_counter(self):
        for _ in range(MAX_PIN_ATTEMPTS - 1):
            with self.assertRaises(InvalidPinError):
                verify_admin_pin("000001")
        verify_admin_pin("482915")
        with self.assertRaises(InvalidPinError) as error:
            verify_admin_pin("000001")
        self.assertNotIsInstance(error.exception, PinLockedError)

    def test_activate_device_returns_the_cashier_account(self):
        self.assertEqual(activate_device("482915"), self.cashier)

    def test_activate_device_without_cashier(self):
        self.cashier.is_active = False
        self.cashier.save()
        with self.assertRaises(NoCashierAvailableError):
            activate_device("482915")

    def test_activate_device_with_wrong_pin(self):
        with self.assertRaises(InvalidPinError):
            activate_device("730264")


@override_settings(PASSWORD_HASHERS=FAST_HASHERS, SGFT_PIN_VERIFIER_ITERATIONS=1000)
class DeactivateUserTests(TestCase):
    """WBS 3.1.5 — las cuentas se desactivan, nunca se borran (autor: Diego)."""

    def setUp(self):
        self.admin = create_user("dueno", "482915", role=Role.ADMIN)

    def test_deactivates_without_deleting(self):
        cashier = create_user("caja", "730264")
        deactivate_user(cashier)
        cashier.refresh_from_db()
        self.assertFalse(cashier.is_active)

    def test_last_active_admin_cannot_be_deactivated(self):
        with self.assertRaises(ValidationError):
            deactivate_user(self.admin)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_an_admin_can_go_if_another_remains(self):
        create_user("socio", "591736", role=Role.ADMIN)
        self.assertFalse(deactivate_user(self.admin).is_active)




@override_settings(PASSWORD_HASHERS=FAST_HASHERS, SGFT_PIN_VERIFIER_ITERATIONS=1000)
class UserAdminTests(TestCase):
    """WBS 3.1.5 — Django Admin de cuentas (autor: Diego)."""

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("root", password="730261")
        self.client.force_login(self.admin)
        self.cashier = create_user("caja", "730264")

    def test_accounts_cannot_be_deleted(self):
        response = self.client.get(reverse("admin:accounts_user_delete", args=[self.cashier.pk]))
        self.assertEqual(response.status_code, 403)
        changelist = self.client.get(reverse("admin:accounts_user_changelist"))
        self.assertNotContains(changelist, "delete_selected")

    def test_deactivate_action(self):
        self.client.post(reverse("admin:accounts_user_changelist"),
                         {"action": "deactivate", "_selected_action": [self.cashier.pk]})
        self.cashier.refresh_from_db()
        self.assertFalse(self.cashier.is_active)

    def test_verifier_is_not_shown(self):
        response = self.client.get(reverse("admin:accounts_user_change", args=[self.cashier.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "pin_verifier")

    def test_saving_a_cashier_as_admin_gives_admin_access(self):
        user = get_user_model().objects.get(pk=self.cashier.pk)
        user.role = Role.ADMIN
        UserAdmin(get_user_model(), site).save_model(None, user, None, True)
        user.refresh_from_db()
        self.assertTrue(user.is_staff)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS, SGFT_PIN_VERIFIER_ITERATIONS=1000)
class AdminLoginLimitTests(TestCase):
    """WBS 4.4 — /admin/login/ comparte el límite de intentos del PIN (checklist-seguridad.md, control 4)."""

    def setUp(self):
        cache.clear()
        self.admin = create_user("dueno", "482915", role=Role.ADMIN)
        self.url = reverse("admin:login")

    def log_in(self, password, username="dueno"):
        return self.client.post(self.url, {"username": username, "password": password, "next": "/admin/"})

    def test_right_password_enters(self):
        self.assertRedirects(self.log_in("482915"), "/admin/", fetch_redirect_response=False)

    def test_five_failures_lock_even_the_right_password(self):
        for _ in range(MAX_PIN_ATTEMPTS - 1):
            self.assertNotContains(self.log_in("000001"), "Demasiados intentos")
        self.assertContains(self.log_in("000001"), "Demasiados intentos. Intenta de nuevo en 15 min.")
        response = self.log_in("482915")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demasiados intentos")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_the_lock_is_shared_with_the_pin(self):
        for _ in range(MAX_PIN_ATTEMPTS):
            with self.assertRaises(InvalidPinError):
                verify_admin_pin("000001")
        self.assertContains(self.log_in("482915"), "Demasiados intentos")
        cache.clear()
        for _ in range(MAX_PIN_ATTEMPTS):
            self.log_in("000001", username="nadie")
        with self.assertRaises(PinLockedError):
            verify_admin_pin("482915")

    def test_success_resets_the_counter(self):
        for _ in range(MAX_PIN_ATTEMPTS - 1):
            self.log_in("000001")
        self.log_in("482915")
        self.client.logout()
        self.assertNotContains(self.log_in("000001"), "Demasiados intentos")

    def test_incomplete_form_neither_counts_nor_resets(self):
        for _ in range(MAX_PIN_ATTEMPTS - 1):
            self.log_in("000001")
        for _ in range(3):
            self.log_in("")
        self.assertContains(self.log_in("000001"), "Demasiados intentos")

    def test_guard_without_user_leaves_the_counter_alone(self):
        self.assertIsNone(guard_admin_login(lambda: None))
        self.assertEqual(pin_minutes_locked(), 0)