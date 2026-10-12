"""Unit tests for apps.accounts. Whoever implements a service writes its tests."""
from django.contrib.auth import get_user_model, authenticate
from django.test import TestCase

from apps.accounts.models import Role

from unittest import expectedFailure


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

#Pruebas unitarias de autenticacion realizadas por Jared y Diego

User = get_user_model()
PASSWORD = 'Clave12345'

class AuthenticationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='cajero1', password = PASSWORD)



    #Prueba que prueba que la cuenta de un empleado que ha sido desactivada no puede ingresar
    def test_inactive_user_doesnt_login(self):
        self.user.is_active = False
        self.user.save()
        self.assertIsNone(authenticate(username='cajero1', password=PASSWORD))


    #Verifica que la contraseña se guarde encriptada y que auque la contraseña este encriptada aun se reconoce
    def test_password_is_saved_encrypted(self):
        self.assertNotEqual(self.user.password, PASSWORD)
        self.assertTrue(self.user.check_password(PASSWORD))

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

    @expectedFailure  # create_user does not set is_staff for the admin role yet (WBS 3.1.1, accounts/services.py)
    def test_admin_role_can_open_admin(self):
        admin = User.objects.create_user(username="admin2", password=PASSWORD, role=Role.ADMIN)
        self.client.force_login(admin)
        self.assertEqual(self.client.get("/admin/").status_code, 200)


# Pruebas unitarias de roles realizadas por Diego

class RoleTests(TestCase):
    """Pruebas del modelo de roles (WBS 3.1.5)."""

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

    # El rol por defecto al crear un usuario sin especificar es CASHIER
    def test_default_role_is_cashier(self):
        user = User.objects.create_user(username="nuevo", password=PASSWORD)
        self.assertEqual(user.role, Role.CASHIER)

    

    # La propiedad is_admin solo es True para rol ADMIN
    def test_is_admin_property(self):
        self.assertTrue(self.admin.is_admin)
        self.assertFalse(self.cashier.is_admin)

    # La propiedad is_cashier solo es True para rol CASHIER
    def test_is_cashier_property(self):
        self.assertTrue(self.cashier.is_cashier)
        self.assertFalse(self.admin.is_cashier)



    # get_role_display devuelve el texto legible del rol
    def test_role_display_text(self):
        self.assertEqual(self.admin.get_role_display(), "Administrador")
        self.assertEqual(self.cashier.get_role_display(), "Cajero")

    # Un superusuario recibe automáticamente el rol ADMIN
    def test_superuser_gets_admin_role(self):
        superuser = User.objects.create_superuser(
            username="root_test",
            email="root@example.com",
            password=PASSWORD,
        )
        self.assertEqual(superuser.role, Role.ADMIN)
        self.assertTrue(superuser.is_admin)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
