from rest_framework import serializers


class VersionedModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            if request.method in ('PATCH', 'PUT'):
                self.fields['version'].required = True
            elif request.method == 'POST':
                self.fields['version'].read_only = True

    def validate_version(self, value):
        request = self.context.get('request')
        if request and request.method in ('PATCH', 'PUT'):
            if value is None:
                raise serializers.ValidationError("Version обязателен для обновления.")
        return value
