"""
Django Admin of the sales (WBS 3.4.9). Owner: Jared; the actions call Jesús's services in apps/pos/services.py.

The quarantine and the review list live here instead of a screen of their own (PLAN, cuts): the Administrator
already uses Django Admin. Everything is read only: a sale is immutable (rule 7) and an operation changes only
through resolve_quarantine and mark_sale_reviewed, which check the role again.
"""
import json

from django.contrib import admin, messages
from django.utils.html import format_html

from apps.pos import services
from apps.pos.models import QuarantinedOperation, QuarantineResolution, QuarantineStatus, Sale


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


def _run(modeladmin, request, queryset, action, done):
    """Applies action to each selected record and reports how many worked and why the others did not."""
    count = 0
    for obj in queryset:
        try:
            action(obj)
        except services.SaleError as error:
            modeladmin.message_user(request, f"{obj}: {error}", messages.ERROR)
        else:
            count += 1
    if count:
        modeladmin.message_user(request, done.format(count=count), messages.SUCCESS)


def _resolution_action(resolution, description):
    def action(modeladmin, request, queryset):
        _run(modeladmin, request, queryset.filter(status=QuarantineStatus.PENDING),
             lambda operation: services.resolve_quarantine(request.user, operation, resolution),
             f"{{count}} operación(es) resuelta(s): {QuarantineResolution(resolution).label.lower()}.")
    action.__name__ = f"resolve_{resolution}"
    return admin.action(description=description)(action)


@admin.register(QuarantinedOperation)
class QuarantinedOperationAdmin(ReadOnlyAdmin):
    list_display = ("device_timestamp", "operation_type", "reason", "user", "status", "resolution", "resolved_by")
    list_filter = ("status", "reason", "operation_type")
    search_fields = ("uuid",)
    date_hierarchy = "device_timestamp"
    fields = ("uuid", "operation_type", "reason", "user", "device_timestamp", "server_timestamp", "content",
              "status", "resolution", "resolved_by", "resolved_at", "sale", "cash_session")
    readonly_fields = fields
    actions = [
        _resolution_action(QuarantineResolution.APPLY, "Aplicar con el catálogo actual"),
        _resolution_action(QuarantineResolution.APPLY_NO_DEDUCTION, "Aplicar sin descontar inventario"),
        _resolution_action(QuarantineResolution.DISCARD, "Descartar (duplicado real)"),
    ]

    @admin.display(description="contenido original")
    def content(self, operation):
        return format_html("<pre>{}</pre>", json.dumps(operation.payload, indent=2, ensure_ascii=False))


class PendingReviewFilter(admin.SimpleListFilter):
    title = "revisión"
    parameter_name = "revision"

    def lookups(self, request, model_admin):
        return [("pendiente", "Pendiente"), ("revisada", "Revisada")]

    def queryset(self, request, queryset):
        if self.value() == "pendiente":
            return queryset.filter(needs_review=True, reviewed_at__isnull=True)
        if self.value() == "revisada":
            return queryset.filter(reviewed_at__isnull=False)
        return queryset


@admin.register(Sale)
class SaleAdmin(ReadOnlyAdmin):
    list_display = ("device_timestamp", "created_by", "payment_method", "charged_total", "server_total",
                    "reasons", "reviewed_by")
    list_filter = (PendingReviewFilter, "payment_method", "cash_session")
    search_fields = ("uuid",)
    date_hierarchy = "device_timestamp"
    fields = ("uuid", "cash_session", "created_by", "payment_method", "charged_total", "server_total", "items",
              "needs_review", "review_reasons", "reviewed_by", "reviewed_at", "device_timestamp", "server_timestamp")
    readonly_fields = fields
    actions = ["mark_reviewed"]

    @admin.display(description="motivos de revisión")
    def reasons(self, sale):
        return ", ".join(sale.review_reasons) or "—"

    @admin.display(description="líneas")
    def items(self, sale):
        return "; ".join(f"{item.quantity} × {item.dish} (${item.unit_price})" for item in sale.order.items.all())

    @admin.action(description="Marcar como revisadas")
    def mark_reviewed(self, request, queryset):
        _run(self, request, queryset, lambda sale: services.mark_sale_reviewed(request.user, sale),
             "{count} venta(s) marcada(s) como revisada(s).")
