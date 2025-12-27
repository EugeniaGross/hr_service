from django.contrib import admin
from unfold.admin import ModelAdmin

from positions.models import Position


@admin.register(Position)
class PositionAdmin(ModelAdmin):
    list_display = ("name_ru",)
    search_fields = ("name_ru",)

    ordering = ("name_ru",)

    list_per_page = 25

    fieldsets = (
        (None, {
            "fields": ("name_ru", "name_fr", "name_en"),
        }),
    )

