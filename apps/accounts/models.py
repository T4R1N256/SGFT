"""Staff accounts (WBS 3.1.1). Only Jesús edits this file."""
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Administrador"
    CASHIER = "cashier", "Cajero"


class StaffUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """A member of the food truck staff. The role drives authorization (RBAC, WBS 3.1.3)."""

    role = models.CharField("rol", max_length=20, choices=Role.choices, default=Role.CASHIER)

    objects = StaffUserManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.get_full_name() or self.username
