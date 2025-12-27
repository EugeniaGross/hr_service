from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api_v1.organizations.views import OrganizationViewSet

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organizations")

urlpatterns = [
    path("", include(router.urls)),
]
