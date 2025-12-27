from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from api_v1.mixins import UpdateModelMixin
from organizations.models import Organization
from api_v1.organizations.serializers import OrganizationSerializer
from api_v1.permissions import IsHRPermission


@extend_schema(tags=["Organizations"])
class OrganizationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    CRUD для справочника организаций.
    """
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsHRPermission]
    
    @extend_schema(
        description=(
            "Получение списка организаций. Доступно hr специалистам."
        )
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Получение информации об организации. Доступно hr специалистам."
        )
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Создание организации. Доступно hr специалистам."
        )
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Частичное изменение данных организации. Доступно hr специалистам."
        )
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Удаление организации. Доступно hr специалистам."
        )
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
