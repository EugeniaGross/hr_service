from django.db import models


class Position(models.Model):
    name_ru = models.CharField(
        "Наименование должности (русский)", 
        max_length=255,
        unique=True,
        blank=True
    )
    name_fr = models.CharField(
        "Наименование должности (французский)", 
        max_length=255,
        unique=True,
        blank=True
    )
    name_en = models.CharField(
        "Наименование должности (английский)", 
        max_length=255,
        unique=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "должность"
        verbose_name_plural = "Должности"
        constraints = [
            models.UniqueConstraint(
                fields=["name_ru"],
                condition=models.Q(name_ru__isnull=False),
                name="unique_not_null_name_ru"
            ),
            models.UniqueConstraint(
                fields=["name_fr"],
                condition=models.Q(name_fr__isnull=False),
                name="unique_not_null_name_fr"
            ),
            models.UniqueConstraint(
                fields=["name_en"],
                condition=models.Q(name_en__isnull=False),
                name="unique_not_null_name_en"
            ),
        ]

    def __str__(self):
        return self.name_ru
