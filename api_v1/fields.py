import base64

from django.core.files.base import ContentFile
from rest_framework import serializers


# class Base64ImageField(serializers.ImageField):
#     def to_internal_value(self, data):
#         if isinstance(data, str) and data.startswith('data:image'):
#             format, imgstr = data.split(';base64,')
#             ext = format.split('/')[-1]
#             data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
#         return super().to_internal_value(data)


import base64
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64FileField(serializers.FileField):
    """
    Поле для приёма файлов, закодированных в Base64.
    Формат данных: "data:<mime_type>;base64,<data>"
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:'):
            try:
                # Разделяем mime-type и данные
                format, file_str = data.split(';base64,')
                # Получаем расширение из mime-type (например: application/pdf -> pdf)
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(file_str), name='temp.' + ext)
            except Exception as e:
                raise serializers.ValidationError(f"Невозможно декодировать файл: {str(e)}")
        return super().to_internal_value(data)
