from django import forms
from django.template.response import TemplateResponse
from django.contrib.admin.helpers import AdminForm
from django.contrib import messages

from unfold.admin import ModelAdmin


class VersionedAdmin(ModelAdmin):
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if hasattr(self.model, "version") and "version" not in form.base_fields:
            form.base_fields["version"] = forms.IntegerField(
                widget=forms.HiddenInput(),
                required=False
            )
        else:
            form.base_fields["version"].widget = forms.HiddenInput()

        return form
    