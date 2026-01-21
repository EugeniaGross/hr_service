from django.conf import settings
from django.db import models
from cryptography.fernet import Fernet

class Organization(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Наименование организации"
    )

    domain = models.CharField(
        max_length=255,
        verbose_name="Домен организации"
    )

    email = models.EmailField(
        verbose_name="Почта организации"
    )

    email_password = models.BinaryField(
        verbose_name="Пароль почты",
        editable=True
    )
    
    email_host = models.CharField(
        max_length=255,
        verbose_name="SMTP-сервер электронной почты"
    )
    email_port = models.PositiveIntegerField(
        verbose_name="Порт SMTP-сервера"
    )

    class Meta:
        verbose_name = "организация"
        verbose_name_plural = "Организации"

    def __str__(self):
        return self.name
    
    def set_password(self, raw_password: str):
        f = Fernet(settings.ENCRYPTION_KEY)
        self.email_password = f.encrypt(raw_password.encode())

    def get_password(self) -> str:
        f = Fernet(settings.ENCRYPTION_KEY)
        return f.decrypt(self.email_password).decode()
