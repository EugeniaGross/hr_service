from django.db import models


class VacancyStatus(models.TextChoices):
    OPEN = "open", "Открыта"
    CLOSED = "closed", "Закрыта"
