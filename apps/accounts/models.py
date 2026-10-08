"""Staff accounts (WBS 3.1.1). Only Jesús edits this file."""
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class Role(models.TextChoices):
    """
    Define los roles operativos del sistema SGFT para el control de acceso (RBAC).
    WBS: 1.2.1 - M-USR: Modelo de usuario, rol y RBAC.
    """
    ADMIN = "admin", "Administrador"
    CASHIER = "cashier", "Cajero"


class StaffUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class StaffUserManager(UserManager):
    """Custom user manager to handle staff and superuser creation cleanly."""
    
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
    
    role = models.CharField(
        "rol",
        max_length=20,
        choices=Role.choices,
        default=Role.CASHIER,
    )

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