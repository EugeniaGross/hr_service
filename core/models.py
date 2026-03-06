from django.db import models
from django.core.exceptions import ValidationError


class VersionedModel(models.Model):
    version = models.PositiveIntegerField(
        "Версия",
        default=1,
    )
    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "Дата обновления",
        auto_now=True,
    )

    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        if self.pk:
            self.version = (self.version or 0) + 1
        super().save(*args, **kwargs)
        
    def clean(self):
        super().clean()
        if self.pk:
            db_obj = self.__class__.objects.filter(pk=self.pk).first()
            if db_obj and db_obj.version != self.version:
                raise ValidationError("Объект был изменён другим пользователем. Обновите страницу.")
