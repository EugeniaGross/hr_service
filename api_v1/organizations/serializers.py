from rest_framework import serializers
from organizations.models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    email_password = serializers.CharField(
        write_only=True,
        required=False,
    )

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "domain",
            "email",
            "email_password",
            "email_host",
            "email_port"
        )

    def create(self, validated_data):
        password = validated_data.pop("email_password", None)
        organization = Organization.objects.create(**validated_data)

        if password:
            organization.set_password(password)
            organization.save(update_fields=["email_password"])

        return organization

    def update(self, instance, validated_data):
        password = validated_data.pop("email_password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
