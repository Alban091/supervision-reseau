from django.contrib import admin

from .models import Device, Port, StatusChange


class PortInline(admin.TabularInline):
    model = Port
    extra = 1
    fields = ["number", "label", "is_open", "last_checked_at"]
    readonly_fields = ["is_open", "last_checked_at"]


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "ip_address", "status", "last_checked_at"]
    list_filter = ["kind", "status"]
    search_fields = ["name", "ip_address"]
    # These fields are written by the supervision loop, so they are only displayed here.
    readonly_fields = ["status", "consecutive_failures", "last_checked_at", "last_seen_at"]
    inlines = [PortInline]


@admin.register(StatusChange)
class StatusChangeAdmin(admin.ModelAdmin):
    list_display = ["changed_at", "device", "old_status", "new_status"]
    list_filter = ["new_status", "device"]
    list_select_related = ["device"]
    date_hierarchy = "changed_at"

    # The history is written by the supervision loop and must not be edited by hand.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
