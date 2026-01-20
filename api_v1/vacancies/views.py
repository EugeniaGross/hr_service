from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend

from api_v1.mixins import UpdateModelMixin
from api_v1.permissions import IsHRPermission
from api_v1.vacancies.filters import VacancyFilter
from api_v1.vacancies.serializers import VacancySerializer
from vacancies.models import Vacancy


@extend_schema(tags=["Vacancies"])
class VacancyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    CRU для справочника подразделений организаций.
    """
    serializer_class = VacancySerializer
    permission_classes = [IsAuthenticated, IsHRPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = VacancyFilter

    def get_queryset(self):
        queryset = (
            Vacancy.objects
            .select_related("department", "department__organization")
            .annotate(candidates_count=Count("candidates"))
            .order_by("-created_at")
        )
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        
    @extend_schema(
        description=(
            "Получение списка вакансий. "
            "Доступно hr специалистам."
        ),
        auth=[],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Получение информации о вакансии. Доступно hr специалистам."
        ),
        auth=[{"ApiKeyAuth": []}],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Создание вакансии. Доступно hr специалистам."
        ),
        auth=[{"ApiKeyAuth": []}],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Частичное изменение данных вакансии. Доступно hr специалистам."
        ),
        auth=[{"ApiKeyAuth": []}],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
