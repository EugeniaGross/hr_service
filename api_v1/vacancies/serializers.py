from rest_framework import serializers

from api_v1.serializers import VersionedModelSerializer
from vacancies.models import Vacancy


class VacancySerializer(VersionedModelSerializer):
    candidates_count = serializers.IntegerField(
        source="candidates.count",
        read_only=True
    )

    class Meta:
        model = Vacancy
        fields = (
            "id",
            "title",
            "code",
            "comment",
            "department",
            # "position",
            "status",
            "opened_at",
            "closed_at",
            "candidates_count",
            "created_at",
            "version"
        )
        read_only_fields = (
            "opened_at",
            "closed_at",
            "created_at",
            "candidates_count",
        )
