from rest_framework import serializers
from django.contrib.auth import get_user_model

from api_v1.fields import Base64FileField
from api_v1.positions.serializers import PositionSerializer
from users.choices import CandidateStatus
from users.models import Candidate, CandidateEducation, CandidateEmployment, CandidateFamilyMember, CandidateRecommendation

User = get_user_model()


class UserLoginSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ("email", "password", "uuid")
        
        
class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    uuid = serializers.UUIDField(write_only=True)
    
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    
class CandidateEducationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = CandidateEducation
        exclude = ("candidate",)
        
        
class CandidateEmploymentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = CandidateEmployment
        exclude = ("candidate",)
        
        
class CandidateFamilyMemberSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = CandidateFamilyMember
        exclude = ("candidate",)
        
        
class CandidateRecommendationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = CandidateRecommendation
        exclude = ("candidate",)
    
    
class CandidateSerializer(serializers.ModelSerializer):
    photo = Base64FileField(use_url=True, required=False, allow_null=True)
    signature = Base64FileField(use_url=True, required=False, allow_null=True)
    organization = serializers.CharField(source="vacancy.department.organization.name")
    department = serializers.CharField(source="vacancy.department.name")
    position = PositionSerializer(source="vacancy.position", read_only=True)
    vacancy = serializers.CharField(source="vacancy.title")
    educations = CandidateEducationSerializer(many=True, required=False)
    employments = CandidateEmploymentSerializer(many=True, required=False)
    family_members = CandidateFamilyMemberSerializer(many=True, required=False)
    recommendations = CandidateRecommendationSerializer(many=True, required=False)

    class Meta:
        model = Candidate
        read_only_fields = (
            "organization",
            "department",
            "position",
            "vacancy",
        )
        fields = (
            "id",
            "photo",
            "organization",
            "department",
            "position",
            "vacancy",
            "first_name",
            "last_name",
            "middle_name",
            "birth_date",
            "birth_place",
            "citizenship",
            "phone",
            "registration_address",
            "residence_address",
            "passport_series",
            "passport_number",
            "passport_issued_by",
            "passport_issued_at",
            "driver_license_number",
            "driver_license_issue_date",
            "driver_license_categories",
            "foreign_languages",
            "recommendations",
            "military_service",
            "disqualification",
            "management_experience",
            "health_restrictions",
            "vacancy_source",
            "acquaintances_in_company",
            "allow_reference_check",
            "job_requirements",
            "work_obstacles",
            "additional_info",
            "salary_expectations",
            "signature",
            "email",
            "educations",
            "employments",
            "family_members",
        )

    def update(self, instance, validated_data):
        educations_data = validated_data.pop("educations", [])
        employments_data = validated_data.pop("employments", [])
        family_members_data = validated_data.pop("family_members", [])
        recommendations_data = validated_data.pop("recommendations", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        def update_nested(instance, nested_data, related_name, model_class):
            existing_objs = {obj.id: obj for obj in getattr(instance, related_name).all()}
            payload_ids = []

            for item in nested_data:
                obj_id = item.get("id")
                if obj_id and obj_id in existing_objs:
                    obj = existing_objs[obj_id]
                    for attr, value in item.items():
                        if attr != "id":
                            setattr(obj, attr, value)
                    obj.save()
                    payload_ids.append(obj_id)
                else:
                    item.pop("id", None)
                    model_class.objects.create(candidate=instance, **item)

            for obj_id, obj in existing_objs.items():
                if obj_id not in payload_ids:
                    obj.delete()


        update_nested(instance, educations_data, "educations", CandidateEducation)
        update_nested(instance, employments_data, "employments", CandidateEmployment)
        update_nested(instance, family_members_data, "family_members", CandidateFamilyMember)
        update_nested(instance, recommendations_data, "recommendations", CandidateRecommendation)

        return instance
    
    
class CandidateCreateSerializer(serializers.ModelSerializer):
    resume_file = Base64FileField(use_url=True, required=False, allow_null=True)

    class Meta:
        model = Candidate
        fields = (
            "first_name",
            "last_name",
            "middle_name",
            "phone",
            "email",
            "language",
            "vacancy",
            "resume_file",
        )
        
    def to_representation(self, instance):
        return CandidateDetailSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class CandidateListSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(source="vacancy.department.organization.name")
    organization_id = serializers.IntegerField(source="vacancy.department.organization.id")
    department = serializers.CharField(source="vacancy.department.name")
    position = PositionSerializer(source="vacancy.position", read_only=True)
    vacancy = serializers.CharField(source="vacancy.title")
    vacancy_id = serializers.IntegerField(source="vacancy.id")
    resume_file = Base64FileField(use_url=True)

    class Meta:
        model = Candidate
        fields = (
            "id",
            "last_name",
            "first_name",
            "middle_name",
            "email",
            "phone",
            "status",
            "organization",
            "organization_id",
            "department",
            "position",
            "vacancy",
            "vacancy_id",
            "anonymization_date",
            "resume_file",
            "created_at",
            "language"
        )


class CandidateDetailSerializer(serializers.ModelSerializer):
    photo = Base64FileField(use_url=True)
    educations = CandidateEducationSerializer(many=True, read_only=True)
    employments = CandidateEmploymentSerializer(many=True, read_only=True)
    family_members = CandidateFamilyMemberSerializer(many=True, read_only=True)
    recommendations = CandidateRecommendationSerializer(many=True, required=False)
    organization = serializers.CharField(source="vacancy.department.organization.name")
    organization_id = serializers.IntegerField(source="vacancy.department.organization.id")
    department = serializers.CharField(source="vacancy.department.name")
    position = PositionSerializer(source="vacancy.position", read_only=True)
    vacancy = serializers.CharField(source="vacancy.title")
    vacancy_id = serializers.IntegerField(source="vacancy.id")
    resume_file = Base64FileField(use_url=True)
    
    class Meta:
        model = Candidate
        fields = (
            "id",
            "organization",
            "organization_id",
            "department",
            "position",
            "vacancy",
            "vacancy_id",
            "status",
            "photo",
            "first_name",
            "last_name",
            "middle_name",
            "birth_date",
            "birth_place",
            "citizenship",
            "phone",
            "registration_address",
            "residence_address",
            "passport_series",
            "passport_number",
            "passport_issued_by",
            "passport_issued_at",
            "driver_license_number",
            "driver_license_issue_date",
            "driver_license_categories",
            "language",
            "foreign_languages",
            "recommendations",
            "military_service",
            "disqualification",
            "management_experience",
            "health_restrictions",
            "vacancy_source",
            "acquaintances_in_company",
            "allow_reference_check",
            "job_requirements",
            "work_obstacles",
            "additional_info",
            "salary_expectations",
            "signature",
            "email",
            "vacancy",
            "created_at",
            "anonymization_date",
            "educations",
            "employments",
            "family_members",
            "resume_file",
        )
    
    
class CandidatePartialUpdateSerializer(serializers.ModelSerializer):
    resume_file = Base64FileField(use_url=True, required=False, allow_null=True)

    class Meta:
        model = Candidate
        fields = (
            "first_name",
            "last_name",
            "middle_name",
            "phone",
            "email",
            "language",
            "vacancy",
            "status",
            "resume_file",
        )
    
    def validate_status(self, value):
        if value == CandidateStatus.ANONYMIZED:
            raise serializers.ValidationError("Нельзя устанавливать статус ANONYMIZED через этот метод")
        return value
