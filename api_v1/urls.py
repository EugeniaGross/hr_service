from django.urls import include, path

extra_patterns = [
    path("", include("api_v1.departments.urls")),
    path("", include("api_v1.organizations.urls")),
    path("", include("api_v1.positions.urls")),
    path("", include("api_v1.vacancies.urls")),
    path("", include("api_v1.users.urls")),
]

urlpatterns = [
    path("", include(extra_patterns)),
]