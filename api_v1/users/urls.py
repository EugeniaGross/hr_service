from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api_v1.users.views import CandidateLinkCheckAPIView, CandidateProfileDetailAPIView, CandidateViewSet, CustomTokenRefreshView, ForgotPasswordAPIView, LoginAPIView, LogoutAPIView, ResetPasswordAPIView, SetPasswordAPIView

router = DefaultRouter()
router.register("candidates", CandidateViewSet, basename="candidat")


urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="refresh_jwt"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("questionnaires/<str:lang>/<uuid:uuid>/", CandidateProfileDetailAPIView.as_view(), name="questionnaire"),
    path("set_password/", SetPasswordAPIView.as_view(), name="set_password"),
    path("forgot_password/", ForgotPasswordAPIView.as_view(), name="forgot_password"),
    path("reset_password/", ResetPasswordAPIView.as_view(), name="reset_password"),
    path("", include(router.urls)),
    path(
        "questionnaires/<str:lang>/<uuid:uuid>/check-link/",
        CandidateLinkCheckAPIView.as_view(),
        name="candidate-link-check"
    ),
]
