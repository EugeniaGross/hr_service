import django_filters
from users.models import Candidate

class CandidateFilter(django_filters.FilterSet):
    position = django_filters.CharFilter(field_name="vacancy__position__name_ru", lookup_expr="icontains")
    organization = django_filters.NumberFilter(field_name="vacancy__department__organization")
    status = django_filters.CharFilter(field_name="status")
    department = django_filters.CharFilter(field_name="vacancy__department__name", lookup_expr="icontains")

    class Meta:
        model = Candidate
        fields = ["vacancy", "position", "organization", "status", "department"]
