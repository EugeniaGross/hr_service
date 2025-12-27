from rest_framework import serializers

from vacancies.models import Vacancy


class VacancySerializer(serializers.ModelSerializer):
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
            "position",
            "status",
            "opened_at",
            "closed_at",
            "candidates_count",
            "created_at",
        )
        read_only_fields = (
            "opened_at",
            "closed_at",
            "created_at",
            "candidates_count",
        )
