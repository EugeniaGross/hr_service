from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from departments.models import Department


@admin.register(Department)
class DepartmentAdmin(ModelAdmin):
    list_display = ("name", "organization", "parent", "colored_level")
    list_filter = ("organization",)
    search_fields = ("name",)
    ordering = ("organization", "level", "name")

    fieldsets = (
        ("Основная информация", {
            "fields": (
                "organization",
                "name",
                "parent",
            )
        }),
        ("Системная информация", {
            "fields": ("level",),
        }),
    )

    readonly_fields = ("level",)

    def colored_level(self, obj):
        color = "red" if obj.level >= 8 else "green"
        return format_html('<b style="color:{}">{}</b>', color, obj.level)

    colored_level.short_description = "Уровень"
