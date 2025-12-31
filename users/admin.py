from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db.models import Case, When, Value, IntegerField

from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin, TabularInline

from users.models import Candidate, CandidateEducation, CandidateEmployment, CandidateFamilyMember, CandidateRecommendation

User = get_user_model()

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    model = User
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    filter_horizontal = ()

    ordering = ("email",)
    list_display = (
        "email",
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_filter = ("role", "is_active", "is_staff")

    search_fields = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Роль", {"fields": ("role",)}),
        ("Права доступа", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "role",
                "is_active",
                "is_staff",
            ),
        }),
    )

    readonly_fields = ("last_login", "date_joined")
    
    
class CandidateEducationInline(TabularInline):
    model = CandidateEducation
    extra = 0
    fields = (
        "institution_name_and_location",
        "graduation_date",
        "education_form",
        "specialty",
        "diploma_information",
    )
    
    class Media:
        css = {
            'all': ('admin/css/admin.css',)
        }
        
        
class CandidateRecommendationInline(TabularInline):
    model = CandidateRecommendation
    extra = 0
    fields = (
        "company",
        "name",
        "position",
        "contact",
        "text",
    )


class CandidateFamilyMemberInline(TabularInline):
    model = CandidateFamilyMember
    extra = 0
    fields = (
        "relation",
        "birth_year",
        "occupation",
        "residence",
    )
    
    
class CandidateEmploymentInline(TabularInline):
    model = CandidateEmployment
    extra = 0
    fields = (
        "position_and_organization",
        "organization_address_and_phone",
        "manager_full_name",
        "start_date",
        "end_date",
        "dismissal_reason",
    )
    
    class Media:
        css = {
            'all': ('admin/css/admin.css',)
        }
        
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            current_job=Case(
                When(end_date__isnull=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-current_job', '-end_date', '-start_date')


@admin.register(Candidate)
class CandidateAdmin(ModelAdmin):
    inlines = [
        CandidateEducationInline,
        CandidateFamilyMemberInline,
        CandidateEmploymentInline,
        CandidateRecommendationInline,
    ]

    list_display = (
        "full_name",
        "phone",
        "vacancy",
        "language",
        "has_user",
        "created_at",
    )

    list_filter = (
        "vacancy",
        "language",
    )

    search_fields = (
        "first_name",
        "last_name",
        "middle_name",
        "phone",
        "passport_number",
    )

    autocomplete_fields = (
        "vacancy",
        "created_by",
        "user",
    )

    readonly_fields = ("created_at",)

    fieldsets = (
        ("ФИО", {
            "fields": (
                "last_name",
                "first_name",
                "middle_name",
            ),
        }),
        ("Персональные данные", {
            "fields": (
                "photo",
                "birth_date",
                "birth_place",
                "citizenship",
            ),
        }),
        ("Контакты", {
            "fields": (
                "phone",
                "registration_address",
                "residence_address",
            ),
        }),
        ("Паспортные данные", {
            "fields": (
                "passport_series",
                "passport_number",
                "passport_issued_by",
                "passport_issued_at",
            ),
        }),
        ("Водительское удостоверение", {
            "fields": (
                "driver_license_number",
                "driver_license_issue_date",
                "driver_license_categories",
            ),
        }),
        ("Профессиональная информация", {
            "fields": (
                "vacancy",
                "language"
            ),
        }),
        ("Анкета", {
            "fields": (
                "foreign_languages",
                "military_service",
                "disqualification",
                "management_experience",
                "health_restrictions",
                "vacancy_source",
                "acquaintances_in_company",
                "allow_reference_check",
                "job_requirements",
                "work_obstacles",
                "additional_info",
            ),
        }),
        ("Заработная плата и подпись", {
            "fields": (
                "salary_expectations",
                "signature",
            ),
        }),
        ("Система", {
            "fields": (
                "user",
                "created_by",
                "created_at",
                "status",
                "link_expiration",
                "anonymization_date"
            ),
        }),
    )

    def full_name(self, obj):
        return f"{obj.last_name} {obj.first_name} {obj.middle_name or ''}".strip()

    full_name.short_description = "ФИО"

    def has_user(self, obj):
        return bool(obj.user)

    has_user.boolean = True
    has_user.short_description = "Есть доступ"

