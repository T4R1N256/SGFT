"""Minimal Django Admin registration so the custom user can be managed from day one.
Account administration screens proper are WBS 3.1.5 (Diego)."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("Rol en SGFT", {"fields": ("role",)}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (("Rol en SGFT", {"fields": ("role",)}),)
    list_display = ("username", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active")
