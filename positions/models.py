from django.db import models


class Position(models.Model):
    name_ru = models.CharField(
        "Наименование должности (русский)", 
        max_length=255,
        blank=True
    )
    name_fr = models.CharField(
        "Наименование должности (французский)", 
        max_length=255,
        blank=True
    )
    name_en = models.CharField(
        "Наименование должности (английский)", 
        max_length=255,
        blank=True
    )
    
    class Meta:
        verbose_name = "должность"
        verbose_name_plural = "Должности"

    def __str__(self):
        return self.name_ru
