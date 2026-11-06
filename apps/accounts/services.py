"""Servicios de cuentas de personal (WBS 3.1.1, 3.1.2, 3.1.5).

Los servicios concentran la lógica de negocio del módulo de usuarios.
Regla del repo: quien escribe el servicio, escribe sus pruebas.
"""
import math

from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import Role, User, is_pin

# Límite de intentos del PIN (WBS 4.4): 5 fallos seguidos bloquean el PIN 15 minutos. Vive en la caché y no en la
# sesión, para que borrar la cookie no lo reinicie. Hay un solo dispositivo, así que el contador es único.
MAX_PIN_ATTEMPTS = 5
PIN_LOCKOUT_MINUTES = 15
_ATTEMPTS_KEY = "accounts:pin_attempts"
_LOCKED_UNTIL_KEY = "accounts:pin_locked_until"


class InvalidPinError(Exception):
    """El PIN no es de ningún Administrador activo."""

    def __init__(self, message="PIN incorrecto."):
        super().__init__(message)


class PinLockedError(InvalidPinError):
    """Demasiados intentos fallidos; minutes_left dice cuánto falta para volver a intentar."""

    def __init__(self, minutes_left):
        self.minutes_left = minutes_left
        super().__init__(f"Demasiados intentos. Intenta de nuevo en {minutes_left} min.")


class NoCashierAvailableError(Exception):
    """No hay una cuenta de cajero activa con la cual activar el dispositivo."""

    def __init__(self, message="No hay una cuenta de cajero activa. Créala en Django Admin."):
        super().__init__(message)


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


def deactivate_user(user):
    """Desactiva una cuenta; nunca se borra (WBS 3.1.5). Siempre debe quedar un Administrador activo."""
    if user.is_admin and not User.objects.filter(role=Role.ADMIN, is_active=True).exclude(pk=user.pk).exists():
        raise ValidationError("Debe quedar al menos un administrador activo.")
    user.is_active = False
    user.save(update_fields=["is_active"])
    return user


def pin_minutes_locked():
    """Minutos que faltan para poder volver a escribir el PIN; 0 si no está bloqueado."""
    until = cache.get(_LOCKED_UNTIL_KEY)
    remaining = (until or 0) - timezone.now().timestamp()
    return math.ceil(remaining / 60) if remaining > 0 else 0


def _register_failure():
    attempts = cache.get(_ATTEMPTS_KEY, 0) + 1
    if attempts >= MAX_PIN_ATTEMPTS:
        cache.set(_LOCKED_UNTIL_KEY, timezone.now().timestamp() + PIN_LOCKOUT_MINUTES * 60, PIN_LOCKOUT_MINUTES * 60)
        cache.delete(_ATTEMPTS_KEY)
    else:
        cache.set(_ATTEMPTS_KEY, attempts, PIN_LOCKOUT_MINUTES * 60)


def verify_admin_pin(pin):
    """
    Devuelve el Administrador activo cuyo PIN (la contraseña de 6 dígitos) es pin.

    Lanza PinLockedError si el PIN está bloqueado por intentos fallidos e InvalidPinError si no coincide; cada
    fallo cuenta para el bloqueo y un acierto reinicia el contador.
    """
    minutes = pin_minutes_locked()
    if minutes:
        raise PinLockedError(minutes)
    if is_pin(pin):
        for admin in User.objects.filter(role=Role.ADMIN, is_active=True):
            if admin.check_password(pin):
                cache.delete(_ATTEMPTS_KEY)
                return admin
    _register_failure()
    minutes = pin_minutes_locked()
    if minutes:
        raise PinLockedError(minutes)
    raise InvalidPinError()


def activate_device(pin):
    """
    Activa el dispositivo (DEC-34): con el PIN de un Administrador devuelve la cuenta de cajero con la que el
    dispositivo queda en sesión permanente. Lanza los mismos errores que verify_admin_pin y, si no hay cajero
    activo, NoCashierAvailableError.
    """
    verify_admin_pin(pin)
    cashier = User.objects.filter(role=Role.CASHIER, is_active=True).order_by("pk").first()
    if cashier is None:
        raise NoCashierAvailableError()
    return cashier