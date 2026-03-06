import base64
import uuid

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
    
    MIME_EXTENSION_MAP = {
        "application/pdf": "pdf",
        "application/msword": "doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.ms-excel": "xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
        "image/jpeg": "jpg",
        "image/png": "png",
    }
    
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:'):
            try:
                format, file_str = data.split(';base64,')
                mime_type = format.split(":")[1]
                ext = self.MIME_EXTENSION_MAP.get(mime_type)
                if not ext:
                    raise serializers.ValidationError(
                        f"Неподдерживаемый тип файла: {mime_type}"
                    )
                file_name = f"{uuid.uuid4()}.{ext}"
                data = ContentFile(base64.b64decode(file_str), name=file_name)
            except Exception as e:
                raise serializers.ValidationError(f"Невозможно декодировать файл: {str(e)}")
        return super().to_internal_value(data)
