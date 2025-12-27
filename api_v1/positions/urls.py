from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api_v1.positions.views import PositionViewSet

router = DefaultRouter()
router.register("positions", PositionViewSet, basename="position")

urlpatterns = [
    path("", include(router.urls)),
]
