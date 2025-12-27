from rest_framework.routers import DefaultRouter

from django.urls import include, path

from api_v1.vacancies.views import VacancyViewSet


router = DefaultRouter()

router.register("vacancies", VacancyViewSet, basename="vacancies")


urlpatterns = [
    path("", include(router.urls)),
]
