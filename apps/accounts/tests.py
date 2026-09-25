"""Unit tests for apps.accounts. Whoever implements a service writes its tests."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Role


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
