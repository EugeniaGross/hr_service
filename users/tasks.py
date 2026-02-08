from celery import shared_task
from django.utils import timezone
import logging

from settings.models import Settings
from users.choices import CandidateStatus
from users.utils import anonymize_name, send_reset_password_email, send_candidate_anonymization_email, send_candidate_questionnaire, send_reset_password_email_hr

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
    retry_backoff=True,
)
def send_reset_password_email_task(self, candidate_id: int, reset_link: str):
    from users.models import Candidate
    try:
        candidate = Candidate.objects.get(id=candidate_id)
    except Candidate.DoesNotExist:
        logger.warning("Candidate %s not found", candidate_id)
        return

    send_reset_password_email(candidate, reset_link)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
    retry_backoff=True,
)
def send_reset_password_email_hr_task(self, user_email: str, reset_link: str, site_url: str):
    """Таск для отправки письма для сброса пароля HR-специалистам"""
    send_reset_password_email_hr(user_email, reset_link, site_url)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    retry_backoff=True,
)
def send_candidate_anonymization_email_task(self, candidate_id: int, first_name: str, last_name: str):
    from users.models import Candidate
    try:
        candidate = Candidate.objects.get(id=candidate_id)
    except Candidate.DoesNotExist:
        logger.warning("Candidate %s not found", candidate_id)
        return

    send_candidate_anonymization_email(candidate, first_name, last_name)
    
    
@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    retry_backoff=True,
)
def send_candidate_questionnaire_task(self, candidate_id: int):
    from users.models import Candidate
    try:
        candidate = Candidate.objects.get(id=candidate_id)
    except Candidate.DoesNotExist:
        logger.warning("Candidate %s not found", candidate_id)
        return
    try:
        send_candidate_questionnaire(candidate)
        logger.info(f"Анкета отправлена на адрес {candidate.email}")
    except Exception as e:
        logger.error("Ошибка при отправке анкеты: %s", e, exc_info=True)
        raise
    
    
    
@shared_task
def daily_anonymization_task():
    """
    Периодическая задача: каждый день в 12:00 проверяет, нужно ли обезличивать кандидатов.
    """
    from users.models import Candidate
    settings_obj = Settings.objects.first()
    if not settings_obj or not settings_obj.anonymization_period_days:
        return

    today = timezone.now().date()
    candidates = Candidate.objects.filter(
        anonymization_date=today
    ).exclude(status__in=[CandidateStatus.ACCEPTED, CandidateStatus.ANONYMIZED])

    for candidate in candidates:
        anonymize_candidate(candidate)


def anonymize_candidate(candidate):
    """
    Обезличивает персональные данные кандидата и блокирует пользователя.
    Также запускает отправку письма кандидату.
    """
    if candidate.status == CandidateStatus.ACCEPTED or candidate.status == CandidateStatus.ANONYMIZED:
        return

    candidate.first_name = anonymize_name(candidate.first_name)
    candidate.last_name = anonymize_name(candidate.last_name)
    candidate.middle_name = anonymize_name(candidate.middle_name)
    candidate.status = CandidateStatus.ANONYMIZED
    candidate.save(update_fields=[
        "first_name", "last_name", "middle_name", "status"
    ])

    user = candidate.user
    user.is_active = False
    user.set_unusable_password()
    user.save(update_fields=["is_active", "password"])

    send_candidate_anonymization_email_task.delay(candidate.id)
