from datetime import timedelta
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from users.choices import CandidateStatus, CommunicationLanguage, EducationForm
from users.managers import UserManager
from users.validators import validate_graduation_year
from vacancies.models import Vacancy


class User(AbstractUser):
    username_validator = None
    username = None
    groups=None
    user_permissions=None
    email = models.EmailField("Электронная почта", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    role = models.CharField(
        "Роль",
        max_length=20,
        choices=[
            ("admin", "Админимстратор"),
            ("hr", "HR специалист"),
            ("candidate", "Кандидат"),
        ]
    )

    objects = UserManager()

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "Пользователи"
        
    def __str__(self) -> str:
        return self.email
        

class Candidate(models.Model):
    status = models.CharField(
        verbose_name="Статус кандидата",
        max_length=20,
        choices=CandidateStatus.choices,
        default=CandidateStatus.NEW,
        db_index=True,
    )
    photo = models.ImageField(
        verbose_name="Фотография кандидата",
        upload_to="candidates/photos/",
        null=True,
        blank=True
    )
    access_uuid = models.UUIDField(
        default=uuid.uuid4, 
        unique=True
    )
    link_expiration = models.DateTimeField(
        "Срок действия ссылки",
        blank=True, 
        null=True
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=100
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=100
    )
    middle_name = models.CharField(
        verbose_name="Отчество",
        max_length=100,
        blank=True
    )
    birth_date = models.DateField("Дата рождения", blank=True, null=True)
    birth_place = models.CharField("Место рождения", max_length=255, blank=True)
    citizenship = models.TextField(
        "Гражданство (в т.ч. другие государства)",
        blank=True
    )
    phone = models.CharField(
        verbose_name="Телефон",
        max_length=20, 
        blank=True
    )
    email = models.EmailField(
        "Электронная почта",
    )
    registration_address = models.CharField(
        "Место регистрации", max_length=255, blank=True
    )
    residence_address = models.CharField(
        "Место проживания", max_length=255, blank=True
    )
    passport_series = models.CharField("Серия паспорта", max_length=10, blank=True)
    passport_number = models.CharField("Номер паспорта", max_length=20, blank=True)
    passport_issued_by = models.CharField("Кем выдан паспорт", max_length=255, blank=True)
    passport_issued_at = models.DateField("Дата выдачи паспорта", blank=True, null=True)
    driver_license_number = models.CharField(
        "Водительское удостоверение №",
        max_length=50,
        blank=True
    )
    driver_license_issue_date = models.DateField(
        "Дата выдачи водительского удостверения",
        null=True,
        blank=True
    )
    driver_license_categories = models.CharField(
        "Разрешенные категории вождения",
        max_length=50,
        blank=True
    )
    language = models.CharField(
        verbose_name="Язык общения",
        max_length=2,
        choices=CommunicationLanguage
    )
    foreign_languages = models.TextField(
        "Владение иностранными языками",
        blank=True,
    )
    military_service = models.TextField(
        "Воинская обязанность (звание, военкомат)",
        blank=True
    )
    disqualification = models.TextField(
        "Дисквалификация / запрет деятельности",
        blank=True
    )
    management_experience = models.TextField(
        "Руководство, предпринимательство, совместительство",
        blank=True
    )
    health_restrictions = models.TextField(
        "Заболевания и ограничения",
        blank=True
    )
    vacancy_source = models.CharField(
        "Источник информации о вакансии",
        max_length=255,
        blank=True
    )
    acquaintances_in_company = models.TextField(
        "Знакомые / родственники в организации",
        blank=True
    )
    allow_reference_check = models.BooleanField(
        "Согласие на запрос рекомендаций по настоящему месту работы",
        blank=True,
        null=True
    )
    job_requirements = models.TextField(
        "Дополнительные требования к работе",
        blank=True
    )
    work_obstacles = models.TextField(
        "Факторы, мешающие работе",
        blank=True
    )
    additional_info = models.TextField(
        "Другие сведения",
        blank=True
    )
    salary_expectations = models.TextField(
        "Пожелания по заработной плате",
        blank=True,
    )
    signature = models.ImageField(
        "Подпись", 
        upload_to="candidates/signatures/",
        blank=True,
        null=True
    )
    resume_file = models.FileField(
        verbose_name="Резюме",
        upload_to="candidates/resume/",
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Создал",
        related_name="created_candidates"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Пользователь",
        related_name="candidate_cards"
    )
    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name="candidates",
        verbose_name="Вакансия"
    )
    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "Дата последнего обновления",
        auto_now=True
    )
    anonymization_date = models.DateField(
        "Дата обезличивания",
        null=True, 
        blank=True
    )

    class Meta:
        verbose_name = "карточка кандидата"
        verbose_name_plural = "Карточки кандидатов"
        
    def is_link_valid(self):
        return timezone.now() <= self.link_expiration
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    
    
class CandidateRecommendation(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="recommendations",
        verbose_name="Кандидат"
    )
    company = models.CharField(
        "Компания",
        max_length=255,
        blank=True
    )
    name = models.CharField(
        "ФИО рекомендателя",
        max_length=255,
        blank=True
    )
    position = models.CharField(
        "Должность рекомендателя",
        max_length=255,
        blank=True
    )
    contact = models.CharField(
        "Телефон или e-mail",
        max_length=255,
        blank=True
    )
    text = models.TextField(
        "Текст рекомендации",
        blank=True
    )

    class Meta:
        verbose_name = "рекомендация"
        verbose_name_plural = "Рекомендации кандидата"
        ordering = ("id",)

    def __str__(self):
        return f"{self.name} ({self.company})"


class CandidateEducation(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="educations"
    )

    institution_name_and_location = models.CharField(
        "Учебное заведение и местонахождение", 
        max_length=255
    )
    graduation_date = models.PositiveIntegerField(
        "Год окончания", 
        validators=[validate_graduation_year]
    )
    education_form = models.CharField(
        "Форма обучения",
        max_length=20,
        choices=EducationForm.choices,
        blank=True
    )
    specialty = models.CharField(
        "Специальность", max_length=255
    )
    diploma_information = models.CharField(
        "Информация о дипломе", 
        max_length=255, 
        blank=True
    )

    class Meta:
        verbose_name = "образование кандидата"
        verbose_name_plural = "Образование кандидата"
        
    def __str__(self):
        return f"{self.institution_name_and_location} - {self.specialty}"
        
        
class CandidateEmployment(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="employments",
        verbose_name="Кандидат"
    )
    start_date = models.DateField(
        "Дата приема",
        null=True,
        blank=True
    )
    end_date = models.DateField(
        "Дата увольнения",
        null=True,
        blank=True
    )
    position_and_organization = models.CharField(
        "Должность и организация",
        max_length=255
    )
    organization_address_and_phone = models.CharField(
        "Контакты организации",
        max_length=255,
        blank=True
    )
    manager_full_name = models.CharField(
        "ФИО руководителя",
        max_length=255,
        blank=True
    )
    dismissal_reason = models.CharField(
        "Причина увольнения",
        max_length=255,
        blank=True
    )

    class Meta:
        verbose_name = "трудовая деятельность"
        verbose_name_plural = "Трудовая деятельность кандидата"
        ordering = ("-end_date",)
        
    def __str__(self):
        return self.position_and_organization
    
        
class CandidateFamilyMember(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="family_members"
    )

    relation = models.CharField(
        "Степень родства", max_length=100
    )
    birth_year = models.PositiveIntegerField(
        "Год рождения", null=True, blank=True
    )
    birth_date = models.DateField(
        "Дата рождения", null=True, blank=True
    )
    occupation = models.CharField(
        "Род деятельности", max_length=255, blank=True
    )
    residence = models.CharField(
        "Место проживания", max_length=255, blank=True
    )

    class Meta:
        verbose_name = "член семьи"
        verbose_name_plural = "Состав семьи кандидата"

    def __str__(self):
        return self.relation
