from django.db import models
from django.utils import timezone

from departments.models import Department
from positions.models import Position
from vacancies.choices import VacancyStatus


class Vacancy(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="vacancies",
        verbose_name="Департамент"
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name="vacancies",
        verbose_name="Должность"
    )
    code = models.CharField("Код", max_length=255)
    title = models.CharField(
        max_length=255,
        verbose_name="Наименование вакансии"
    )
    comment = models.TextField("Комментарий", blank=True)
    status = models.CharField(
        verbose_name="Статус",
        max_length=10,
        choices=VacancyStatus.choices,
        default=VacancyStatus.OPEN
    )
    opened_at = models.DateField(
        verbose_name="Дата открытия",
        editable=False
    )
    closed_at = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата закрытия"
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="vacancies",
        verbose_name="Создатель"
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "Дата последнего обновления",
        auto_now=True
    )
    
    class Meta:
        verbose_name = "вакансия"
        verbose_name_plural = "Вакансии"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.opened_at = timezone.now().date()

        if self.status == VacancyStatus.CLOSED and not self.closed_at:
            self.closed_at = timezone.now().date()

        if self.status == VacancyStatus.OPEN:
            self.closed_at = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
