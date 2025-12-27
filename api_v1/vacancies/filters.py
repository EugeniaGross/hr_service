import django_filters
from vacancies.models import Vacancy
from vacancies.choices import VacancyStatus

class VacancyFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=VacancyStatus.choices
    )

    class Meta:
        model = Vacancy
        fields = ("status",)
