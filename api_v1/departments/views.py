from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from api_v1.departments.serializers import DepartmentSerializer, DepartmentTreeSerializer
from api_v1.mixins import UpdateModelMixin
from api_v1.permissions import IsHRPermission
from departments.models import Department


@extend_schema(tags=["Departments"])
class DepartmentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    CRUD для справочника подразделений организаций.
    """
    serializer_class = DepartmentTreeSerializer
    permission_classes = [IsAuthenticated, IsHRPermission]

    def get_queryset(self):
        organization_id = self.kwargs["organization_id"]
        if self.action == "list":
            return (
                Department.objects
                .filter(
                    organization_id=organization_id,
                    parent__isnull=True,
                )
                .prefetch_related(
                    "children__children__children__children__children__children__children"
                )
                .order_by("name")
            )
        return Department.objects.filter(organization_id=organization_id)
        
    def get_serializer_class(self):
        if self.action == "list":
            return DepartmentTreeSerializer
        return DepartmentSerializer

    def perform_create(self, serializer):
        organization_id = self.kwargs["organization_id"]
        serializer.save(organization_id=organization_id)
        
    @extend_schema(
        description=(
            "Получение списка подразделений организации. "
            "Возращает деревья главных подразделений. "
            "Доступно hr специалистам."
        )
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Получение информации об подразделении организации. Доступно hr специалистам."
        )
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Создание подразделения организации. Доступно hr специалистам."
        )
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Частичное изменение данных подразделения организации. Доступно hr специалистам."
        )
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Удаление подразделения организации. Доступно hr специалистам."
        )
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
