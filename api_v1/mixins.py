from django.conf import settings
from django.db.models.query import prefetch_related_objects
from rest_framework.response import Response


class UpdateModelMixin:
    """
    Update a model instance.
    """

    def partial_update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        queryset = self.filter_queryset(self.get_queryset())
        if queryset._prefetch_related_lookups:
            instance._prefetched_objects_cache = {}
            prefetch_related_objects([instance], *queryset._prefetch_related_lookups)

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


class CookiesTokenMixin:

    def add_refresh_token_in_cookies(self, response):
        if response.status_code == 200:
            data = response.data
            refresh_token = data.get("refresh")

            cookie_max_age = 3600 * 24 * settings.REFRESH_TOKEN_LIFETIME

            response.set_cookie(
                key=settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"],
                value=refresh_token,
                httponly=True,
                secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
                samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
                max_age=cookie_max_age,
                path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
            )

            del response.data["refresh"]
        return response
