"""Django Admin of staff accounts (WBS 3.1.5): the only place where accounts are created, changed and deactivated.
Accounts are never deleted; is_staff follows the role (accounts.services)."""
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError

from .models import Role, User
from .services import deactivate_user


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name", "email")}),
        ("Rol en SGFT", {"fields": ("role", "is_active")}),
        ("Permisos de Django", {"classes": ("collapse",), "fields": ("is_staff", "is_superuser", "groups")}),
        ("Fechas", {"fields": ("last_login", "date_joined", "pin_changed_at")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (("Rol en SGFT", {"fields": ("role", "first_name", "last_name")}),)
    readonly_fields = ("is_staff", "last_login", "date_joined", "pin_changed_at")
    list_display = ("username", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active")
    actions = ["deactivate"]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def save_model(self, request, obj, form, change):
        # Same invariant as change_role(): only Administrators (and superusers) enter Django Admin.
        obj.is_staff = obj.role == Role.ADMIN or obj.is_superuser
        super().save_model(request, obj, form, change)

    @admin.action(description="Desactivar las cuentas seleccionadas")
    def deactivate(self, request, queryset):
        done = 0
        for user in queryset.filter(is_active=True):
            try:
                deactivate_user(user)
                done += 1
            except ValidationError as error:
                self.message_user(request, f"{user}: {error.messages[0]}", messages.ERROR)
        if done:
            self.message_user(request, f"Cuentas desactivadas: {done}.", messages.SUCCESS)