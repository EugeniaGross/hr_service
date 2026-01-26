from datetime import datetime
import tempfile
import os

from docxtpl import InlineImage, DocxTemplate
from docx.shared import Mm 
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status, viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from rest_framework.decorators import action
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from django.http import FileResponse

from api_v1.mixins import CookiesTokenMixin, UpdateModelMixin
from api_v1.permissions import IsCandidateWithValidLink, IsHRPermission
from api_v1.users.filters import CandidateFilter
from api_v1.users.serializers import CandidateCreateSerializer, CandidateDetailSerializer, CandidateListSerializer, CandidatePartialUpdateSerializer, ResetPasswordSerializer, CandidateSerializer, ForgotPasswordSerializer, SetPasswordSerializer, UserLoginSerializer
from api_v1.users.utils import RU_MONTHS, EN_MONTHS, FR_MONTHS, get_questionnaire_ru_xlsx, get_questionnaire_en_xlsx, get_questionnaire_fr_xlsx, DocumentService
from users.models import Candidate
from users.choices import CandidateStatus, CommunicationLanguage
from users.tasks import send_reset_password_email_task, send_candidate_anonymization_email_task, send_candidate_questionnaire_task
from users.utils import anonymization_candidate_date, calculate_candidate_link_expiration, anonymize_name

User = get_user_model()


@extend_schema(tags=["Auth"])
class LoginAPIView(CookiesTokenMixin, APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    @extend_schema(
        description=("Получение JWT токена. Для входа кандидата необходимо передать uuid"),
        responses=inline_serializer(
            name="AccessTokenSchema", fields={"access": serializers.CharField(), "type": serializers.CharField()}
        ),
    )
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        uuid = request.data.get("uuid")

        if not email or not password:
            return Response({"detail": "Email и пароль обязательны"}, status=400)
        
        if uuid:
            self.check_candidate(uuid)
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({"detail": "Неверные учетные данные"}, status=401)
        if user and not uuid and user.role != "hr":
            return Response({"detail": "Доступ запрещен"}, status=403)
        response = self._get_tokens_for_user(user)
        return self.add_refresh_token_in_cookies(response, user.role)
    
    def check_candidate(self, uuid):
        try:
            profile = Candidate.objects.get(access_uuid=uuid)
        except Candidate.DoesNotExist:
            return Response({"detail": "Ссылка недействительна"}, status=404)
        if not profile.is_link_valid():
            return Response({"detail": "Срок действия ссылки кандидата истек"}, status=403)
        user = profile.user
        if not user.has_usable_password():
            return Response({"detail": "Пароль ещё не установлен"}, status=400)
        
    def _get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "type": "Bearer",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Auth"])
class CustomTokenRefreshView(CookiesTokenMixin, TokenRefreshView):
    permission_classes = []
    serializer_class = None

    @extend_schema(
        description=("Обновление JWT токена"),
        responses=inline_serializer(
            name="AccessTokenSchema", fields={"access": serializers.CharField()}
        ),
        request={},
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response(
                {"detail": "Refresh токен не найден в cookies."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)
        return self.add_refresh_token_in_cookies(response)
    
    
@extend_schema(tags=["Auth"])
class LogoutAPIView(APIView):

    @extend_schema(
        description=("Удаление JWT токена"),
        responses={204: None},
        request={},
    )
    def post(self, request):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
        return response


@extend_schema(tags=["Questionnaires"])
class CandidateProfileDetailAPIView(APIView):
    permission_classes = [IsCandidateWithValidLink]
    serializer_class = CandidateSerializer

    def get_object(self, **kwargs):
        """
        Возвращает объект Candidate по UUID и lang или None
        """
        uuid = self.kwargs.get("uuid")
        lang = self.kwargs.get("lang")
        try:
            return Candidate.objects.get(access_uuid=uuid, language=lang)
        except Candidate.DoesNotExist:
            return None

    @extend_schema(description="Получение анкеты кандидата. Доступно кандидатам.")
    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile is None:
            return Response({"detail": "Кандидат не найден"}, status=404)
        user = profile.user
        if not user.has_usable_password():
            return Response({"password_set": False}, status=200)
        serializer = CandidateSerializer(profile, context={"request": self.request})
        return Response(serializer.data)

    @extend_schema(description="Изменение анкеты кандидата. Доступно кандидатам.")
    def patch(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile is None:
            return Response({"detail": "Кандидат не найден"}, status=404)
        serializer = CandidateSerializer(profile, data=request.data, partial=True, context={"request": self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if profile.status != CandidateStatus.RECEIVED:
            profile.status = CandidateStatus.RECEIVED
            profile.save(update_fields=["status"])
        return Response(serializer.data, status=200)


@extend_schema(tags=["Auth"])
class SetPasswordAPIView(CookiesTokenMixin, APIView):
    permission_classes = [AllowAny]
    serializer_class = SetPasswordSerializer

    @extend_schema(
        description=("Установка пароля. Необходимо передать uuid из ссылки на анкету кандидата"),
    )
    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uuid = serializer.validated_data["uuid"]
        try:
            profile = Candidate.objects.get(access_uuid=uuid)
        except Candidate.DoesNotExist:
            return Response({"detail": "Ссылка недействительна"}, status=404)

        if not profile.is_link_valid():
            return Response({"detail": "Срок действия ссылки кандидата истёк"}, status=403)

        user = profile.user
        if user.has_usable_password():
            return Response({"detail": "Пароль уже установлен"}, status=400)

        user.set_password(serializer.validated_data["password"])
        user.is_active = True
        user.save()

        response = self._get_tokens_for_user(user)
        return self.add_refresh_token_in_cookies(response)

    def _get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "type": "Bearer",
            },
            status=status.HTTP_200_OK,
        )
        

@extend_schema(tags=["Auth"])        
class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer

    @extend_schema(
        description=("Сброс пароля. Необходимо передать uuid из ссылки на анкету кандидата"),
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uuid = serializer.validated_data["uuid"]
        email = serializer.validated_data["email"]
        try:
            profile = Candidate.objects.get(access_uuid=uuid, user__email=email)
        except Candidate.DoesNotExist:
            return Response({"detail": "Письмо для сброса пароля отправлено"}, status=200)
        if not profile.is_link_valid():
            return Response({"detail": "Срок действия ссылки кандидата истёк"}, status=403)
        user = profile.user
        token = default_token_generator.make_token(user)
        domain = profile.vacancy.department.organization.domain
        reset_link = f"https://{domain}/questionnaires/{profile.language}/{uuid}/reset_password?token={token}"
        send_reset_password_email_task.delay(profile.id, reset_link)
        return Response({"detail": "Письмо для сброса пароля отправлено"}, status=200)


@extend_schema(tags=["Auth"])
class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    @extend_schema(
        description=("Установка нового пароля. Необходимо передать uuid из ссылки на анкету кандидата и token для восстановления пароля"),
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uuid = serializer.validated_data["uuid"]
        try:
            profile = Candidate.objects.get(access_uuid=uuid)
        except Candidate.DoesNotExist:
            return Response({"detail": "Ссылка недействительна"}, status=404)
        if not profile.is_link_valid():
            return Response({"detail": "Срок действия ссылки кандидата истёк"}, status=403)
        user = profile.user
        token = serializer.validated_data["token"]
        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Ссылка для сброса пароля недействительна или устарела"}, status=403)
        user.set_password(serializer.validated_data["password"])
        user.save()
        return Response({"detail": "Пароль успешно установлен"}, status=200)


@extend_schema(tags=["Candidats"]) 
class CandidateViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated, IsHRPermission]
    queryset = Candidate.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = CandidateFilter
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CandidateListSerializer
        if self.action == 'create':
            return CandidateCreateSerializer
        if self.action == 'retrieve':
            return CandidateDetailSerializer
        if self.action == 'partial_update':
            return CandidatePartialUpdateSerializer
    
    @transaction.atomic
    def perform_create(self, serializer):
        email = serializer.validated_data["email"]
        user, created = User.objects.get_or_create(
            email=email,
            role="candidate",
            defaults={"is_active": False}
        )
        if created:
            user.set_unusable_password()
            user.save()
        serializer.save(
            user=user,
            created_by=self.request.user,
            link_expiration=calculate_candidate_link_expiration(),
            anonymization_date=anonymization_candidate_date()
        )
        
    @transaction.atomic
    def perform_update(self, serializer):
        candidate = self.get_object()
        new_email = serializer.validated_data.get("email")
        old_user = candidate.user
        if new_email and new_email != old_user.email:
            user, created = User.objects.get_or_create(
                email=new_email,
                defaults={"is_active": False}
            )
            if created:
                user.set_unusable_password()
                user.save()
            candidate.user = user
            serializer.save(user=user, status=CandidateStatus.NEW)
        else:
            serializer.save(
                status = CandidateStatus.NEW
            )
        
    @action(detail=True, methods=["get"])
    def get_questionnaire_pdf(self, request, pk=None):
        candidate = self.get_object()
        path = str(settings.BASE_DIR) + os.sep
        if candidate.language == CommunicationLanguage.RU:
            tpl = DocxTemplate(
                os.path.join(path, "templates", "Анкета_ru.docx")
            )
        if candidate.language == CommunicationLanguage.EN:
            tpl = DocxTemplate(
                os.path.join(path, "templates", "Анкета_en.docx")
            )
        if candidate.language == CommunicationLanguage.FR:
            tpl = DocxTemplate(
                os.path.join(path, "templates", "Анкета_fr.docx")
            )
        date = candidate.updated_at
        photo = None
        sign = None

        if candidate.photo:
            photo = InlineImage(
                tpl,
                candidate.photo.path,
                width=Mm(24)
            )

        if candidate.signature:
            sign = InlineImage(
                tpl,
                candidate.signature.path,
                width=Mm(24) 
            )
        allow_reference_check = ""
        if candidate.allow_reference_check:
            allow_reference_check = "Да"
        if not candidate.allow_reference_check:
            allow_reference_check = "Нет"
        context = {
            "candidate": candidate,
            "day": date.day,
            "year": date.year,
            "photo": photo,
            "signature": sign,
            "allow_reference_check": allow_reference_check
        }
        if candidate.language == CommunicationLanguage.RU:
            context["month"] = RU_MONTHS[date.month]
        if candidate.language == CommunicationLanguage.FR:
            context["month"] = FR_MONTHS[date.month]
        if candidate.language == CommunicationLanguage.EN:
            context["month"] = EN_MONTHS[date.month]
        pdf_bytes = DocumentService().get_doc_pdf(context, tpl)
        return FileResponse(
            pdf_bytes,
            as_attachment=True,
            filename="Анкета.pdf",
        )
        
    @action(detail=True, methods=["get"])
    def get_consent_pdf(self, request, pk=None):
        candidate = self.get_object()
        path = str(settings.BASE_DIR) + os.sep
        if candidate.language == CommunicationLanguage.RU:
            tpl = DocxTemplate(os.path.join(path, "templates", "Текст для согласия рус.docx"))
        if candidate.language == CommunicationLanguage.EN:
            tpl = DocxTemplate(os.path.join(path, "templates", "Текст для согласия англ.docx"))
        if candidate.language == CommunicationLanguage.FR:
            tpl = DocxTemplate(os.path.join(path, "templates", "Текст для согласия франц.docx"))
        context = {
            "candidate": candidate,
        }
        pdf_bytes = DocumentService().get_doc_pdf(context, tpl)
        return FileResponse(
            pdf_bytes,
            as_attachment=True,
            filename="Согласие на обработку персональных данных.pdf",
        )

    @action(detail=True, methods=["get"])
    def get_questionnaire_xlsx(self, request, pk=None):
        candidate = self.get_object()
        if candidate.language == CommunicationLanguage.RU:
            template_path = os.path.join(settings.BASE_DIR, "templates", "RUS_2025.xlsx")
            tmp = get_questionnaire_ru_xlsx(candidate, template_path)
            filename = f"Анкета_{candidate.last_name}_{candidate.first_name}.xlsx"
        if candidate.language == CommunicationLanguage.EN:
            template_path = os.path.join(settings.BASE_DIR, "templates", "ENG_2025.xlsx")
            tmp = get_questionnaire_en_xlsx(candidate, template_path)
            filename = f"Application_form_{candidate.last_name}_{candidate.first_name}.xlsx"
        if candidate.language == CommunicationLanguage.FR:
            template_path = os.path.join(settings.BASE_DIR, "templates", "FRA_2025.xlsx")
            tmp = get_questionnaire_fr_xlsx(candidate, template_path)
            filename = f"Formulaire_{candidate.last_name}_{candidate.first_name}.xlsx"

        return FileResponse(
            open(tmp.name, "rb"),
            as_attachment=True,
            filename=filename,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    @extend_schema(
        description=(
            "Отправка ссылки на анкету кандидату. Доступно hr специалистам."
        )
    )
    @action(detail=True, methods=["post"])
    def send_questionnaire(self, request, pk=None):
        candidate = self.get_object()
        
        if candidate.status == CandidateStatus.SENT:
            return Response({"detail": "Анкета уже отправлена"}, status=status.HTTP_400_BAD_REQUEST)
        send_candidate_questionnaire_task.delay(candidate.id)
        return Response({"detail": "Анкета успешно отправлена"}, status=status.HTTP_200_OK)
    
    @extend_schema(
        description=(
            "Обезличивание персональных данных кандидата. Доступно hr специалистам."
        )
    )
    def destroy(self, request, *args, **kwargs):
        candidate = self.get_object()
        candidate.anonymize()
        return Response(
            {"detail": "Персональные данные кандидата успешно обезличены."},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        description=(
            "Получение списка кандидатов. Доступно hr специалистам."
        )
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Получение информации о кандидате. Доступно hr специалистам."
        )
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Создание кандидата. Доступно hr специалистам."
        )
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        description=(
            "Частичное изменение данных кандидата. Доступно hr специалистам."
        )
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


@extend_schema(tags=["Questionnaires"])
class CandidateLinkCheckAPIView(APIView):
    """
    Проверка валидности ссылки кандидата и статуса пароля.
    Доступно без токена.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        description=(
            "Проверка ссылки на анкету. Возвращает информацию о валидности и установлен ли пароль у кандидата."
        )
    )
    def get(self, request, uuid: str, lang: str):
        try:
            candidate = Candidate.objects.get(access_uuid=uuid, language=lang)
        except Candidate.DoesNotExist:
            return Response({"valid": False}, status=status.HTTP_404_NOT_FOUND)

        link_valid = candidate.is_link_valid()
        password_set = candidate.user.has_usable_password() if candidate.user else False

        return Response(
            {
                "valid": link_valid,
                "password_set": password_set,
            },
            status=status.HTTP_200_OK
        )