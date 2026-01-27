from rest_framework import permissions
from api_v1.utils import decode_candidate_jwt
from users.models import Candidate


class IsCandidateWithValidLink(permissions.BasePermission):
    message = "Ссылка недействительна или срок истёк"

    def has_permission(self, request, view):
        uuid_str = (
            view.kwargs.get("uuid")
            or request.query_params.get("uuid")
        )
        lang = (
            view.kwargs.get("lang")
            or request.query_params.get("lang")
        )
        if not uuid_str:
            return False
        
        if not lang:
            return False
        
        if request.auth.access_uuid != uuid_str and request.auth.language != lang:
            return False
        
        return request.auth.is_link_valid()
    
    def has_object_permission(self, request, view, obj):
        """
        Проверка на уровне объекта:
        - кандидат может редактировать только свою анкету
        - ссылка должна быть действительна
        """
        if not isinstance(obj, Candidate):
            return False
        
        if request.auth.id != obj.id:
            return False

        return obj.is_link_valid()


class IsHRPermission(permissions.BasePermission):
    """
    Доступ разрешён только аутентифицированным пользователям с ролью 'hr'
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "hr"
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
