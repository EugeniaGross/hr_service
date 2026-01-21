from django.contrib import admin
from django import forms
from unfold.admin import ModelAdmin
from unfold.forms import UnfoldAdminPasswordInput

from organizations.models import Organization


class OrganizationAdminForm(forms.ModelForm):
    email_password = forms.CharField(
        label="Пароль почты",
        widget=UnfoldAdminPasswordInput(render_value=True),
        required=False
    )

    class Meta:
        model = Organization
        exclude = ('email_password',)
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['email_password'].help_text = (
                'Оставьте пустым, если не хотите менять пароль'
            )
            self.fields['email_password'].widget.attrs.update(
                {'placeholder': '************'}
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get("email_password")
        if password:
            instance.set_password(password)
        if commit:
            instance.save()
        return instance



@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    form = OrganizationAdminForm

    list_display = ("name", "domain", "email")
    search_fields = ("name", "domain", "email")
    ordering = ("name",)

    fieldsets = (
        ("Основная информация", {"fields": ("name", "domain")}),
        ("Почтовые настройки", {"fields": ("email", "email_host", "email_password", "email_port")}),
    )
