from rest_framework.routers import DefaultRouter

from django.urls import include, path

from api_v1.departments.views import DepartmentViewSet


router = DefaultRouter()

router.register(
    r"organizations/(?P<organization_id>\d+)/departments",
    DepartmentViewSet,
    basename="departments",
)

urlpatterns = [
    path("", include(router.urls)),
]
