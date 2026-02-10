from rest_framework import serializers
from positions.models import Position


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = "__all__"
        
    def validate(self, attrs):
        for field in ("name_ru", "name_fr", "name_en"):
            value = attrs.get(field)
            if value:
                if Position.objects.filter(**{field: value}).exists():
                    raise serializers.ValidationError({
                        field: "Такое значение уже существует"
                    })
        return attrs
