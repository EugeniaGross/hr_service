import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
if settings.DEBUG:
    os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')
    
app = Celery(
    'backend',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "daily-anonymization-12": {
        "task": "users.tasks.daily_anonymization_task",
        "schedule": crontab(hour=12, minute=0),
    },
}