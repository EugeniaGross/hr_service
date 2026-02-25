from rest_framework import serializers
from positions.models import Position


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = "__all__"
        
    def _validate_unique_name(self, field_name, value):
        qs = Position.objects.filter(**{field_name: value})
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Такое значение уже существует.")
        return value

    def validate_name_ru(self, value):
        return self._validate_unique_name("name_ru", value)

    def validate_name_fr(self, value):
        return self._validate_unique_name("name_fr", value)

    def validate_name_en(self, value):
        return self._validate_unique_name("name_en", value)
