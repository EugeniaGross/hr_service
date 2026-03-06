from django.contrib import admin

from core.admin import VersionedAdmin
from settings.models import Settings


@admin.register(Settings)
class SettingsAdmin(VersionedAdmin):
    list_display = (
        "link_expiration_hours",
        "anonymization_period_days",
        "updated_at",
    )

    readonly_fields = ("updated_at",)

    fieldsets = (
        ("Ссылки", {
            "fields": ("link_expiration_hours",),
        }),
        ("Персональные данные", {
            "fields": ("anonymization_period_days",),
        }),
        ("Служебная информация", {
            "fields": ("updated_at", "version"),
        }),
    )

    def has_add_permission(self, request):
        """
        Запрещаем создание второй записи настроек
        """
        return not Settings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """
        Запрещаем удаление настроек
        """
        return False
