import uuid
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import jwt

from users.models import CandidateRefreshToken
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


def decode_candidate_jwt(token: str) -> dict:
    """
    Декодирует JWT токен кандидата и возвращает payload.
    Бросает исключение, если токен недействителен или просрочен.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SIMPLE_JWT["SIGNING_KEY"],
            algorithms=["HS256"],
        )
        if payload.get("type") != "candidate_access":
            raise InvalidTokenError("Некорректный тип токена")
        return payload
    except ExpiredSignatureError:
        raise ExpiredSignatureError("Срок действия токена истёк")
    except InvalidTokenError:
        raise InvalidTokenError("Неверный токен")


class CandidatePasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, candidate, timestamp):
        return f"{candidate.pk}{candidate.password}{timestamp}"


candidate_token_generator = CandidatePasswordResetTokenGenerator()


def generate_candidate_jwt_access_token(candidate):
    now = timezone.now()
    payload = {
        "type": "candidate_access",
        "token_type": "access",
        "candidate_id": candidate.id,
        "exp": now + settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
        "iat": now,
    }
    return jwt.encode(payload, settings.SIMPLE_JWT["SIGNING_KEY"], algorithm="HS256")


def generate_candidate_jwt_refresh_token(candidate):
    token_id = uuid.uuid4().hex
    now = timezone.now()
    payload = {
        "type": "candidate_access",
        "token_type": "refresh",
        "jti": token_id,
        "candidate_id": candidate.id,
        "exp": now + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
        "iat": now,
    }

    token = jwt.encode(payload, settings.SIMPLE_JWT["SIGNING_KEY"], algorithm="HS256")

    CandidateRefreshToken.objects.create(
        candidate=candidate,
        token=token_id,
        expires_at=now + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
    )

    return token
