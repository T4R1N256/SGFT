"""Unit tests for apps.accounts. Whoever implements a service writes its tests."""
import base64
import hashlib

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.accounts.models import DEFAULT_PIN_VERIFIER_ITERATIONS, Role


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
