from django.db import models
from django.core.validators import MinValueValidator


class Settings(models.Model):
    """Глобальные настройки системы."""

    link_expiration_hours = models.PositiveIntegerField(
        verbose_name="Срок действия ссылки (часы)",
        validators=[MinValueValidator(1)],
        help_text="Через сколько часов ссылка становится недействительной"
    )

    anonymization_period_days = models.PositiveIntegerField(
        verbose_name="Срок обезличивания персональных данных (дней)",
        validators=[MinValueValidator(1)],
        help_text="Через сколько дней персональные данные должны быть обезличены",
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(
        verbose_name="Обновлено",
        auto_now=True
    )

    class Meta:
        verbose_name = "Настройки системы"
        verbose_name_plural = "Настройки системы"
