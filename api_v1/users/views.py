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
from openpyxl import load_workbook
from django.db.models import Case, When, Value, IntegerField

from api_v1.mixins import CookiesTokenMixin, UpdateModelMixin
from api_v1.permissions import IsCandidateWithValidLink, IsHRPermission
from api_v1.users.filters import CandidateFilter
from api_v1.users.serializers import CandidateCreateSerializer, CandidateDetailSerializer, CandidateListSerializer, CandidatePartialUpdateSerializer, ResetPasswordSerializer, CandidateSerializer, ForgotPasswordSerializer, SetPasswordSerializer, UserLoginSerializer
from api_v1.users.utils import RU_MONTHS, insert_employment_row, insert_family_row, insert_recommendation_row, write_cell, split_text, insert_education_row, write_recommendation_cell, find_row_by_text, write_answer_block, write_created_at, insert_candidate_photo, DocumentService
from users.models import Candidate
from users.choices import CandidateStatus
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
        return self.add_refresh_token_in_cookies(response)
    
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
        
    @action(detail=True, methods=["get"])
    def get_questionnaire_pdf(self, request, pk=None):
        candidate = self.get_object()
        path = str(settings.BASE_DIR) + os.sep
        tpl = DocxTemplate(os.path.join(path, "templates", "Анкета_ru.docx"))
        now = datetime.now()
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
            "day": now.day,
            "month": RU_MONTHS[now.month],
            "year": now.year,
            "photo": photo,
            "signature": sign,
            "allow_reference_check": allow_reference_check,
        }
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
        tpl = DocxTemplate(os.path.join(path, "templates", "Текст для согласия рус.docx"))
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
        template_path = os.path.join(settings.BASE_DIR, "templates", "RUS_2025.xlsx")
        wb = load_workbook(template_path)
        ws = wb.active
        passport_value = ", ".join(filter(None, [
            candidate.passport_series,
            candidate.passport_number,
            f"выдан {candidate.passport_issued_by}" if candidate.passport_issued_by else None,
            candidate.passport_issued_at.strftime("%d.%m.%Y") if candidate.passport_issued_at else None,
        ]))
        write_cell(ws, 2, 7, candidate.vacancy.position.name_ru) 
        write_cell(ws, 5, 3, candidate.last_name)               
        write_cell(ws, 6, 3, candidate.first_name)             
        write_cell(ws, 7, 3, candidate.middle_name)           
        write_cell(ws, 9, 3, candidate.birth_date.strftime("%d.%m.%Y") if candidate.birth_date else "")
        write_cell(ws, 10, 9, candidate.citizenship)        
        write_cell(ws, 11, 5, candidate.birth_place)        

        passport_lines = split_text(passport_value, max_len=55, max_lines=2)
        if passport_lines:
            write_cell(ws, 12, 8, passport_lines[0])
        if len(passport_lines) > 1:
            write_cell(ws, 13, 1, passport_lines[1])

        write_cell(ws, 14, 6, candidate.phone)                  
        write_cell(ws, 15, 6, candidate.email)                    

        registration_lines = split_text(candidate.registration_address, max_len=60, max_lines=3)
        for i, line in enumerate(registration_lines):
            write_cell(ws, 16 + i, 6, line)

        residence_lines = split_text(candidate.residence_address, max_len=60, max_lines=3)
        for i, line in enumerate(residence_lines):
            write_cell(ws, 19 + i, 6, line)
        start_row = 24
        educations = candidate.educations.all().order_by("graduation_date")
        num_educations = educations.count()
        extra_rows_needed = max(0, num_educations - 4)

        for i in range(extra_rows_needed):
            insert_education_row(ws, start_row + 4 + i)

        for idx, edu in enumerate(educations):
            row = start_row + idx
            ws.cell(row=row, column=1).value = edu.institution_name_and_location  
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)

            ws.cell(row=row, column=6).value = edu.graduation_date
            ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=7)

            ws.cell(row=row, column=8).value = edu.get_education_form_display()
            ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=9)

            ws.cell(row=row, column=10).value = edu.specialty
            ws.merge_cells(start_row=row, start_column=10, end_row=row, end_column=12)

            ws.cell(row=row, column=13).value = edu.diploma_information
            ws.merge_cells(start_row=row, start_column=13, end_row=row, end_column=14)

        end_of_education_row = start_row + max(num_educations, 4)
        start_employment_row = end_of_education_row + 2

        employments = candidate.employments.annotate(
            current_job=Case(
                When(end_date__isnull=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-current_job', '-end_date', '-start_date')
        num_employments = employments.count()
        extra_rows_needed = max(0, num_employments - 7)
        for i in range(extra_rows_needed):
            insert_employment_row(ws, start_employment_row + 5 + i)

        for idx, emp in enumerate(employments):
            row = start_employment_row + idx
            ws.cell(row=row, column=1).value = emp.start_date.strftime("%d.%m.%Y") if emp.start_date else ""
            ws.cell(row=row, column=2).value = emp.end_date.strftime("%d.%m.%Y") if emp.end_date else ""
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
            ws.cell(row=row, column=5).value = emp.position_and_organization
            ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=7)
            ws.cell(row=row, column=8).value = emp.organization_address_and_phone
            ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=9)
            ws.cell(row=row, column=10).value = emp.manager_full_name
            ws.merge_cells(start_row=row, start_column=10, end_row=row, end_column=12)
            ws.cell(row=row, column=13).value = emp.dismissal_reason
            ws.merge_cells(start_row=row, start_column=13, end_row=row, end_column=14)
        end_of_employment_row = start_employment_row + max(num_employments, 7)

        start_foreign_languages_row = end_of_employment_row + 1 
        foreign_languages_text = candidate.foreign_languages
        lines = split_text(foreign_languages_text, max_len=75, max_lines=4)

        first_row_height = ws.row_dimensions[start_foreign_languages_row].height

        for i, line in enumerate(lines):
            write_cell(ws, start_foreign_languages_row + i, 1, line)
        for i in range(4):
            ws.row_dimensions[start_foreign_languages_row + i].height = first_row_height
        for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row and row[0] and "Рекомендации с предыдущих мест работы" in str(row[0]):
                recommendations_start_row = i + 1 
                break
        else:
            recommendations_start_row = ws.max_row + 1

        recommendations = candidate.recommendations.all()
        num_recommendations = recommendations.count()
        extra_rows_needed = max(0, num_recommendations - 4)

        for i in range(extra_rows_needed):
            insert_recommendation_row(ws, recommendations_start_row + 4 + i)

        for idx, rec in enumerate(recommendations):
            row = recommendations_start_row + idx
            write_recommendation_cell(ws, row, rec.text)
            
        for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row and row[0] and "Состав семьи, близкие родственники" in str(row[0]):
                family_start_row = i + 2
                break
        else:
            family_start_row = ws.max_row + 1
        family_members = candidate.family_members.all()
        num_family = family_members.count()
        extra_rows_needed = max(0, num_family - 8)
        for i in range(extra_rows_needed):
            insert_family_row(ws, family_start_row + 8 + i)
        for idx, member in enumerate(family_members):
            row = family_start_row + idx
            ws.cell(row=row, column=1).value = member.relation
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
            ws.cell(row=row, column=4).value = member.birth_year
            ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=6)
            ws.cell(row=row, column=7).value = member.occupation
            ws.merge_cells(start_row=row, start_column=7, end_row=row, end_column=10)
            ws.cell(row=row, column=11).value = member.residence
            ws.merge_cells(start_row=row, start_column=11, end_row=row, end_column=14)

        write_answer_block(
            ws,
            "Являетесь ли Вы военнообязанным",
            candidate.military_service,
            max_lines=2
        )
        write_answer_block(
            ws,
            "Действует ли в отношении Вас запрет",
            candidate.disqualification,
            max_lines=2
        )
        write_answer_block(
            ws,
            "Являетесь (являлись) ли Вы руководителем",
            candidate.management_experience,
            max_lines=3
        )
        write_answer_block(
            ws,
            "Имеете ли Вы (или члены Вашей семьи) заболевания",
            candidate.health_restrictions,
            max_lines=3
        )
        driver_row = find_row_by_text(
            ws,
            "Водительское удостоверение №"
        )

        if driver_row:
            ws.cell(row=driver_row, column=8).value = candidate.driver_license_number
            ws.merge_cells(
                start_row=driver_row,
                start_column=8,
                end_row=driver_row,
                end_column=9
            )
            ws.cell(row=driver_row, column=13).value = (
                candidate.driver_license_issue_date.strftime("%d.%m.%Y")
                if candidate.driver_license_issue_date else ""
            )
            ws.merge_cells(
                start_row=driver_row,
                start_column=13,
                end_row=driver_row,
                end_column=14
            )

            categories_row = driver_row + 1
            ws.cell(row=categories_row, column=6).value = candidate.driver_license_categories
            ws.merge_cells(
                start_row=categories_row,
                start_column=6,
                end_row=categories_row,
                end_column=14
            )
        write_answer_block(
            ws,
            "Источник информации о вакансии",
            candidate.vacancy_source,
            max_lines=1
        )
        write_answer_block(
            ws,
            "Знакомые, родственники, работающие в нашей организации",
            candidate.acquaintances_in_company,
            max_lines=1
        )
        write_answer_block(
            ws,
            "Согласны ли Вы на обращение по вашему настоящему месту работы",
            (
                "Да"
                if candidate.allow_reference_check is True
                else "Нет"
                if candidate.allow_reference_check is False
                else ""
            ),
            max_lines=1
        )
        write_answer_block(
            ws,
            "Дополнительные требования к новому месту работы",
            candidate.job_requirements,
            max_lines=3
        )

        write_answer_block(
            ws,
            "Какие факторы могут стать или являются для Вас помехой в работе",
            candidate.work_obstacles,
            max_lines=3
        )
        write_answer_block(
            ws,
            "Другие сведения, которые Вы хотите сообщить о себе",
            candidate.additional_info,
            max_lines=3
        )
        write_answer_block(
            ws,
            "Ваши пожелания по заработной плате",
            candidate.salary_expectations,
            max_lines=1
        )
        write_created_at(ws, candidate)
        if candidate.photo:
            insert_candidate_photo(ws, candidate.photo.path)
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        wb.save(tmp.name)
        tmp.seek(0)

        filename = f"Анкета_{candidate.last_name}_{candidate.first_name}.xlsx"

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
        candidate.first_name = anonymize_name(candidate.first_name)
        candidate.last_name = anonymize_name(candidate.last_name)
        candidate.middle_name = anonymize_name(candidate.middle_name)
        candidate.anonymization_date = timezone.now()
        candidate.status = CandidateStatus.ANONYMIZED
        candidate.save()
        candidate.user.is_active = False
        candidate.user.set_unusable_password()
        candidate.user.save()
        candidate.user.save(update_fields=["is_active", "password"])
        send_candidate_anonymization_email_task.delay(candidate.id)
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