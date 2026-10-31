"""Servicios de cuentas de personal (WBS 3.1.1).

Los servicios concentran la lógica de negocio del módulo de usuarios.
Regla del repo: quien escribe el servicio, escribe sus pruebas.
"""
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import Role, User


def create_user(username, password, role=Role.CASHIER, **extra_fields):
    """Crea un usuario validando la contraseña y sincronizando is_staff con el rol.

    Reglas (WBS 3.1.1):
      - La contraseña pasa por validate_password() (validadores de Django).
      - Si el rol es ADMIN, is_staff se activa automáticamente para poder entrar
        al Django Admin, que es donde se administran las cuentas de personal.

    Devuelve la instancia de User recién creada.
    """
    validate_password(password)
    extra_fields["role"] = role
    extra_fields["is_staff"] = role == Role.ADMIN
    return User.objects.create_user(username=username, password=password, **extra_fields)


def change_role(user, role):
    """Cambia el rol de un usuario y sincroniza is_staff en consecuencia.

    Mantiene la invariante: role == ADMIN  ⇔  is_staff == True.

    Devuelve la instancia de User actualizada.
    """
    user.role = role
    user.is_staff = role == Role.ADMIN or user.is_superuser
    user.save(update_fields=["role", "is_staff"])
    return user


class InvalidPinError(Exception):
    """El PIN no coincide con una cuenta administradora activa."""


class NoCashierAvailableError(Exception):
    """No existe una cuenta de cajero activa."""


def activate_device(pin):
    """Valida el PIN de un administrador y devuelve una cuenta de cajero activa.

    No devuelve ni revela qué administrador validó el PIN.
    """
    if not isinstance(pin, str) or len(pin) != 6 or not pin.isascii() or not pin.isdigit():
        raise InvalidPinError

    admins = User.objects.filter(
        role=Role.ADMIN,
        is_active=True,
    )

    valid_pin = False

    # No detenernos en el primer administrador evita revelar cuál coincidió
    # mediante una diferencia obvia en el número de comprobaciones.
    for admin in admins.iterator():
        if admin.check_password(pin):
            valid_pin = True

    if not valid_pin:
        raise InvalidPinError

    cashier = User.objects.filter(
        role=Role.CASHIER,
        is_active=True,
    ).first()

    if cashier is None:
        raise NoCashierAvailableError

    return cashier
