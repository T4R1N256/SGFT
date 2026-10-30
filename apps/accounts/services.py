"""Servicios de cuentas de personal (WBS 3.1.1).

Los servicios concentran la lógica de negocio del módulo de usuarios.
Regla del repo: quien escribe el servicio, escribe sus pruebas.
"""
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache

from apps.accounts.models import Role, User

CACHE_KEY_PIN_ATTEMPTS = "sgft_pin_attempts"
PIN_MAX_ATTEMPTS = 5
PIN_LOCKOUT_SECONDS = 15 * 60  # 15 minutos


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


class PinLockedError(InvalidPinError):
    """Se superaron los intentos fallidos permitidos."""


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


# --- Bloqueo por caché y nuevas funciones (Tarea de Diego) ---


def _check_pin_lockout():
    """Lanza PinLockedError si se excedieron los intentos."""
    attempts = cache.get(CACHE_KEY_PIN_ATTEMPTS, 0)
    if attempts >= PIN_MAX_ATTEMPTS:
        raise PinLockedError("Demasiados intentos. Espera 15 minutos.")


def _register_failed_attempt():
    """Suma un intento fallido. Si se llega al máximo, se queda bloqueado hasta que expire."""
    try:
        cache.incr(CACHE_KEY_PIN_ATTEMPTS)
    except ValueError:
        # Si la llave no existe, incr lanza ValueError
        cache.set(CACHE_KEY_PIN_ATTEMPTS, 1, timeout=PIN_LOCKOUT_SECONDS)


def verify_admin_pin(pin):
    """Devuelve el Administrador al que corresponde el PIN, o lanza error."""
    _check_pin_lockout()

    if not isinstance(pin, str) or len(pin) != 6 or not pin.isascii() or not pin.isdigit():
        _register_failed_attempt()
        raise InvalidPinError

    admins = User.objects.filter(role=Role.ADMIN, is_active=True)
    for admin in admins.iterator():
        if admin.check_password(pin):
            cache.delete(CACHE_KEY_PIN_ATTEMPTS)  # Éxito, limpiamos intentos
            return admin

    _register_failed_attempt()
    raise InvalidPinError


def deactivate(user):
    """Desactiva la cuenta sin borrarla de la base de datos."""
    user.is_active = False
    user.save(update_fields=["is_active"])
    return user