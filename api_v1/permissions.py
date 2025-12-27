from rest_framework import permissions
from users.models import Candidate


class IsCandidateWithValidLink(permissions.BasePermission):
    message = "Ссылка недействительна или срок истёк"

    def has_permission(self, request, view):
        print(request.user.is_authenticated)
        if not request.user.is_authenticated:
            return False

        if request.user.role != "candidate":
            return False

        uuid_str = (
            view.kwargs.get("uuid")
            or request.query_params.get("uuid")
        )

        if not uuid_str:
            return False

        try:
            profile = Candidate.objects.get(
                user=request.user,
                access_uuid=uuid_str
            )
        except Candidate.DoesNotExist:
            return False

        return profile.is_link_valid()
    
    def has_object_permission(self, request, view, obj):
        """
        Проверка на уровне объекта:
        - кандидат может редактировать только свою анкету
        - ссылка должна быть действительна
        """
        if not isinstance(obj, Candidate):
            return False

        if obj.user != request.user:
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
