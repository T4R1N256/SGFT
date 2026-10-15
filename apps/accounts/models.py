"""Staff accounts (WBS 3.1.1). Owner: Jesús, who reviews every change; whoever writes a model generates its migration after telling him (DEC-37)."""
import base64
import hashlib
import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone

PIN_LENGTH = 6
# PBKDF2-SHA256 iterations of the offline verifier (pin-administrador-sin-red.md). Tests may lower it with the
# SGFT_PIN_VERIFIER_ITERATIONS setting; production keeps the default.
DEFAULT_PIN_VERIFIER_ITERATIONS = 600_000


def is_pin(raw_password):
    """True for exactly six ASCII digits: the only passwords that can be typed in the PIN boxes."""
    return isinstance(raw_password, str) and len(raw_password) == PIN_LENGTH and raw_password.isascii() \
        and raw_password.isdigit()


class Role(models.TextChoices):
    """
    Define los roles operativos del sistema SGFT para el control de acceso (RBAC).
    WBS: 1.2.1 - M-USR: Modelo de usuario, rol y RBAC.
    """
    ADMIN = "admin", "Administrador"
    CASHIER = "cashier", "Cajero"


class StaffUserManager(UserManager):
    """Custom user manager to handle staff and superuser creation cleanly."""

    def _create_user_object(self, username, email, password, **extra_fields):
        # Django assigns make_password() directly; going through set_password() also derives the offline verifier.
        user = super()._create_user_object(username, email, None, **extra_fields)
        user.set_password(password)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    A member of the food truck staff. The role drives authorization (RBAC, WBS 3.1.3). Accounts are deactivated
    with is_active, never deleted.

    The admin PIN is the account password: 6 digits, hashed by Django like any password (check_password). For
    opening the till without network the device downloads a verifier per active Administrator:
    PBKDF2-SHA256(PIN, pin_verifier_salt, pin_verifier_iterations), base64. It can only be computed when the
    password is set, the only moment the server knows it, so set_password stores it here. A password that is not
    6 digits gets no verifier. Which verifiers the device receives (active Administrators only) is decided by the
    view that serves them.
    """

    role = models.CharField(
        "rol",
        max_length=20,
        choices=Role.choices,
        default=Role.CASHIER,
    )
    pin_changed_at = models.DateTimeField("cambio del PIN", null=True, blank=True)
    pin_verifier_salt = models.CharField("sal del verificador sin red", max_length=32, blank=True)
    pin_verifier_iterations = models.PositiveIntegerField("iteraciones del verificador sin red", default=0)
    pin_verifier = models.CharField("verificador sin red", max_length=64, blank=True)

    objects = StaffUserManager()

    class Meta:
        db_table = "users"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_cashier(self):
        return self.role == Role.CASHIER

    @property
    def has_offline_verifier(self):
        return bool(self.pin_verifier)

    def set_password(self, raw_password):
        """Hashes the password, as Django does, and derives the offline verifier if it is a 6-digit PIN. Does not save."""
        super().set_password(raw_password)
        if is_pin(raw_password):
            iterations = getattr(settings, "SGFT_PIN_VERIFIER_ITERATIONS", DEFAULT_PIN_VERIFIER_ITERATIONS)
            salt = secrets.token_bytes(16)
            verifier = hashlib.pbkdf2_hmac("sha256", raw_password.encode(), salt, iterations)
            self.pin_verifier_salt = base64.b64encode(salt).decode()
            self.pin_verifier_iterations = iterations
            self.pin_verifier = base64.b64encode(verifier).decode()
        else:
            self._clear_offline_verifier()
        self.pin_changed_at = timezone.now()

    def set_unusable_password(self):
        super().set_unusable_password()
        self._clear_offline_verifier()
        self.pin_changed_at = timezone.now()

    def _clear_offline_verifier(self):
        self.pin_verifier_salt = ""
        self.pin_verifier_iterations = 0
        self.pin_verifier = ""
