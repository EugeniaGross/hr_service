from rest_framework import authentication
from rest_framework import exceptions
from api_v1.utils import decode_candidate_jwt
from users.models import Candidate

class CandidateJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            return None

        token = parts[1]
        try:
            payload = decode_candidate_jwt(token)
        except Exception:
            raise exceptions.AuthenticationFailed("Неверный токен")
        
        if payload.get("token_type") != "access" or payload.get("type") != "candidate_access":
            raise exceptions.AuthenticationFailed("Неверный токен")

        candidate_id = payload.get("candidate_id")
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            raise exceptions.AuthenticationFailed("Кандидат не найден")

        return (candidate.user, candidate)
