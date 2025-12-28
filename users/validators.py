from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_graduation_year(value):
    current_year = timezone.now().year
    if value < current_year - 60:
        raise ValidationError(f"Год окончания не может быть меньше {current_year - 60}")
    if value > current_year:
        raise ValidationError(f"Год окончания не может быть больше {current_year}")