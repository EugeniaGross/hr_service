from django.contrib import admin
from unfold.admin import ModelAdmin

from vacancies.models import Vacancy


@admin.register(Vacancy)
class VacancyAdmin(ModelAdmin):
    list_display = (
        "title",
        "department",
        "status",
        "opened_at",
        "closed_at",
        "created_by",
    )

    list_filter = (
        "status",
        "department",
    )

    search_fields = (
        "title",
    )

    readonly_fields = (
        "opened_at",
        "closed_at",
        "created_at",
    )

    fieldsets = (
        ("Основная информация", {
            "fields": (
                "title",
                "department",
                "position",
                "status",
            )
        }),
        ("Системные даты", {
            "fields": (
                "opened_at",
                "closed_at",
                "created_at",
            )
        }),
        ("Служебная информация", {
            "fields": (
                "created_by",
            )
        }),
    )

    autocomplete_fields = (
        "department",
        "created_by",
    )
