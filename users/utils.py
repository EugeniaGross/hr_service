from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail.backends.smtp import EmailBackend

from organizations.models import Organization
from settings.models import Settings
from users.choices import CandidateStatus, CommunicationLanguage

EMAIL_QUESTIONNAIRE_TEMPLATES = {
    "ru": "email_template_ru.html",
    "en": "email_template_en.html",
    "fr": "email_template_fr.html",
}

EMAIL_ANONYMIZATION_TEMPLATES = {
    "en": "email_destroy_en.html",
    "fr": "email_destroy_fr.html",
    "ru": "email_destroy_ru.html"
}

EMAIL_RESET_PASSWORD_TEMPLATES = {
    "ru": "email_reset_password_ru.html",
    "en": "email_reset_password_en.html",
    "fr": "email_reset_password_fr.html",
}

def get_reset_password_template(language: str) -> str:
    return EMAIL_RESET_PASSWORD_TEMPLATES.get(
        language, EMAIL_RESET_PASSWORD_TEMPLATES["ru"]
    )
    
def get_reset_password_template(language: str) -> str:
    return EMAIL_RESET_PASSWORD_TEMPLATES.get(
        language, EMAIL_RESET_PASSWORD_TEMPLATES["ru"]
    )

def get_email_questionnaire_template(language: str) -> str:
    return EMAIL_QUESTIONNAIRE_TEMPLATES.get(
        language, EMAIL_QUESTIONNAIRE_TEMPLATES["ru"]
    )


def get_email_anonymization_template(language: str) -> str:
    return EMAIL_ANONYMIZATION_TEMPLATES.get(
        language, EMAIL_ANONYMIZATION_TEMPLATES["en"]
    )


def get_organization_email_connection(org: Organization):
    if org.email_port == 465:
        return EmailBackend(
            host=org.email_host,
            port=org.email_port,
            username=org.email,
            password=org.get_password(),
            use_ssl=True,
            fail_silently=False,
        )
    return EmailBackend(
        host=org.email_host,
        port=org.email_port,
        username=org.email,
        password=org.get_password(),
        use_tls=True,
        fail_silently=False,
    )


def send_candidate_questionnaire(candidate):
    organization = candidate.vacancy.department.organization
    link = build_candidate_link(candidate)
    template_name = get_email_questionnaire_template(candidate.language)
    context = {
        "name": candidate.first_name,
        "organization_name": organization,
        "url": link,
    }
    html_body = render_to_string(template_name, context)
    if candidate.language == CommunicationLanguage.FR:
        subject = "Questionnaire du candidat"
    elif candidate.language == CommunicationLanguage.EN:
        subject = "Candidate questionnaire"
    else:
        subject = "Анкета кандидата"
    email = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=organization.email,
        to=[candidate.user.email],
        connection=get_organization_email_connection(organization),
    )

    email.attach_alternative(html_body, "text/html")
    email.send()
    candidate.status = CandidateStatus.SENT
    candidate.save(update_fields=["status"])
    
    
def send_candidate_anonymization_email(candidate, first_name, last_name):
    organization = candidate.vacancy.department.organization
    template_name = get_email_anonymization_template(candidate.language)
    context = {
        "organization_name": organization,
        "first_name": first_name,
        "last_name": last_name,
    }
    html_body = render_to_string(template_name, context)
    if candidate.language == CommunicationLanguage.FR:
        subject = "Suppression des données personnelles"
    elif candidate.language == CommunicationLanguage.EN:
        subject = "Personal data deletion notification"
    else:
        subject = "Уведомление об удалении персональных данных"
    email = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=organization.email,
        to=[candidate.user.email],
        connection=get_organization_email_connection(organization),
    )
    email.attach_alternative(html_body, "text/html")
    email.send()
    
    
def send_reset_password_email(candidate, reset_link: str):
    organization = candidate.vacancy.department.organization

    template_name = get_reset_password_template(candidate.language)
    context = {
        "organization_name": organization,
        "reset_link": reset_link,
    }

    html_body = render_to_string(template_name, context)
    if candidate.language == CommunicationLanguage.FR:
        subject = "Réinitialisation du mot de passe"
    elif candidate.language == CommunicationLanguage.EN:
        subject = "Password reset"
    else:
        subject = "Сброс пароля"

    email = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=organization.email,
        to=[candidate.user.email],
        connection=get_organization_email_connection(organization),
    )

    email.attach_alternative(html_body, "text/html")
    email.send()


def calculate_candidate_link_expiration() -> timezone.datetime | None:
    settings = Settings.objects.first()
    hours = settings.link_expiration_hours if settings else 72
    return (timezone.now() + timedelta(hours=hours)).date()


def anonymization_candidate_date():
    settings = Settings.objects.first()
    days = settings.anonymization_period_days if settings else 0
    if days:
        return (timezone.now() + timedelta(days=days)).date()
    return None


def build_candidate_link(candidate) -> str:
    organization = candidate.vacancy.department.organization

    domain = organization.domain.rstrip("/")
    lang = candidate.language
    uuid = candidate.access_uuid

    return f"https://{domain}/{lang}/questionnaires/{uuid}/"


def anonymize_name(name: str) -> str:
    """Оставляем первую букву, остальные заменяем на *"""
    if not name:
        return ""
    return name[0] + "*" * (len(name) - 1)


def send_reset_password_email_hr(user_email: str, reset_link: str, site_url: str):
    """Отправка письма для сброса пароля HR-специалистам"""

    template_name = "email_reset_password_hr.html"
    context = {
        "site_url": site_url,
        "reset_link": reset_link,
    }

    html_body = render_to_string(template_name, context)
    subject = "Сброс пароля"
    email = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=settings.EMAIL_HOST_USER,
        to=[user_email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)
