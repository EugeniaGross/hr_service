import django_filters
from vacancies.models import Vacancy
from vacancies.choices import VacancyStatus

class VacancyFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=VacancyStatus.choices
    )
    organization = django_filters.NumberFilter(
        field_name="department__organization"
    )

    class Meta:
        model = Vacancy
        fields = ("status", "organization")
