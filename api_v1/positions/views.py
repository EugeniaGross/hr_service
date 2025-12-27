from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from api_v1.mixins import UpdateModelMixin
from positions.models import Position
from api_v1.positions.serializers import PositionSerializer
from api_v1.permissions import IsHRPermission


@extend_schema(tags=["Positions"])
class PositionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    CRUD для справочника должностей.
    """
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated, IsHRPermission]
    
    @extend_schema(
        description=(
            "Получение списка должностей. Доступно hr специалистам."
        )
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Получение информации об должности. Доступно hr специалистам."
        )
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Создание должности. Доступно hr специалистам."
        )
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Частичное изменение должности. Доступно hr специалистам."
        )
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Удаление должности. Доступно hr специалистам."
        )
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
