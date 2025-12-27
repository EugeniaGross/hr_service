from django.db import models
from django.forms import ValidationError

from organizations.models import Organization


class Department(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="departments",
        verbose_name="Организация"
    )

    name = models.CharField(
        max_length=255,
        verbose_name="Наименование подразделения"
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
        verbose_name="Подразделение уровнем выше"
    )

    level = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Уровень вложенности"
    )

    class Meta:
        unique_together = ("organization", "parent", "name")
        verbose_name = "подразделение"
        verbose_name_plural = "Подразделения"
        
    def __str__(self):
        return f"{self.organization.name} / {self.name}"

    def clean(self):
        if self.parent:
            if self.parent.organization != self.organization:
                raise ValidationError("Подразделение должно быть в той же организации")

            if self.parent.level >= 8:
                raise ValidationError("Максимальная глубина подразделений — 8 уровней")

            self.level = self.parent.level + 1
        else:
            self.level = 1
