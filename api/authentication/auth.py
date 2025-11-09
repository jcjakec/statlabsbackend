from ninja.security import HttpBearer
from ninja.errors import HttpError
from .utility import decode_token
from services.users.models import User

class TokenAuthentication(HttpBearer):
    def authenticate(self, request, token: str):
        payload = decode_token(token)
        if payload and payload["user"] and payload["type"] == "access":
            return payload["user"]
        else:
            return None
