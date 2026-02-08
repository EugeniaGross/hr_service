from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db.models import Case, When, Value, IntegerField

from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin, TabularInline

from users.choices import CandidateStatus
from users.models import Candidate, CandidateCitizenship, CandidateEducation, CandidateEmployment, CandidateFamilyMember, CandidateRecommendation

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
        "is_staff",
        "is_superuser",
    )
    list_filter = ("role", "is_staff", "is_superuser",)

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
    
    def get_fieldsets(self, request, obj=None):
        """Если объект — кандидат, убираем поле password"""
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.role == "candidate":
            fieldsets = list(fieldsets)
            new_fieldsets = []
            for name, options in fieldsets:
                fields = list(options.get("fields", []))
                if "password" in fields:
                    fields.remove("password")
                if "is_active" in fields:
                    fields.remove("is_active")
                new_fieldsets.append((name, {"fields": fields}))
            return new_fieldsets
        return fieldsets
    
    
class CandidateCitizenshipInline(TabularInline):
    model = CandidateCitizenship
    extra = 0
    fields = (
        "citizenship",
        "passport_series",
        "passport_number",
        "passport_issued_by",
        "passport_issued_at",
    )
    
    
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
        "birth_date",
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
        CandidateCitizenshipInline,
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
    )

    autocomplete_fields = (
        "vacancy",
        "created_by",
        "user",
    )

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Персональные данные", {
            "fields": (
                "last_name",
                "first_name",
                "middle_name",
                "photo",
                "birth_date",
                "birth_place",
            ),
        }),
        ("Контакты и адрес", {
            "fields": (
                "email",
                "phone",
                "registration_address",
                "residence_address",
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
                "language",
                "resume_file",
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
                "salary_expectations",
            ),
        }),
        ("Подпись", {
            "fields": (
                "signature",
            ),
        }),
        ("Система", {
            "fields": (
                "user",
                "created_by",
                "created_at",
                "updated_at",
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
    
    def save_model(self, request, obj, form, change):
        if change:
            old = Candidate.objects.get(pk=obj.pk)

            if (
                old.status != CandidateStatus.ANONYMIZED
                and obj.status == CandidateStatus.ANONYMIZED
            ):
                obj.anonymize()
                return

        super().save_model(request, obj, form, change)
