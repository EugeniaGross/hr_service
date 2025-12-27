from django.db import models


class CommunicationLanguage(models.TextChoices):
    EN = "en", "Английский"
    FR = "fr", "Французский"
    RU = "ru", "Русский"


class EducationForm(models.TextChoices):
    FULL_TIME = "full", "Дневная"
    EVENING = "evening", "Вечерняя"
    DISTANCE = "distance", "Заочная"
    
    
class CandidateStatus(models.TextChoices):
    NEW = "new", "Новый"
    SENT = "sent", "Анкета отправлена"
    RECEIVED = "received", "Анкета получена"
    ACCEPTED = "accepted", "Принят"
    ARCHIVED = "archived", "В архиве"
    ANONYMIZED = "anonymized", "Обезличено"
