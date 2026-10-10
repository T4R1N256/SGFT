"""Unit tests for apps.accounts. Whoever implements a service writes its tests."""
from django.contrib.auth import get_user_model, authenticate
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

#Pruebas unitarias de autenticacion realizadas por Jared y Diego

User = get_user_model()
PASSWORD = 'Clave12345'

class AuthenticationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='cajero1', password = PASSWORD)

    #Prueba de inicio de sesion correctos
    def test_correct_credentials(self):
        self.assertEqual(authenticate(username='cajero1', password=PASSWORD),self.user)

    #Prueba de datos de incio de sesion incorrectos
    def test_incorrect_credentials(self):
        self.assertIsNone(authenticate(username='cajero1',password='incorrecta'))

    #Prueba de usuario no existente en el sistema
    def test_nonexistent_user(self):
        self.assertIsNone(authenticate(username='nadie', password=PASSWORD))

    #Prueba de campos vacios en el formulario
    def test_empty_fields(self):
        self.assertIsNone(authenticate(username='', password=''))

    #Prueba que prueba que la cuenta de un empleado que ha sido desactivada no puede ingresar
    def test_inactive_user_doesnt_login(self):
        self.user.is_active = False
        self.user.save()
        self.assertIsNone(authenticate(username='cajero1', password=PASSWORD))

    #Prueba de login y logout
    def test_login_logout(self):
        self.assertTrue(self.client.login(username='cajero1', password=PASSWORD))
        self.assertIn("_auth_user_id", self.client.session)
        self.client.logout()
        self.assertNotIn("_auth_user_id",self.client.session)

    
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

