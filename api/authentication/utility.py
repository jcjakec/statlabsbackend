import jwt
from datetime import datetime, timezone
from . import settings
from .models import RefreshToken, AuthToken
from services.users.models import User

# Generate token
# Generating a refresh token deletes the old refresh token if it exists

def generate_token(user, token_type: str):
    expiry = datetime.now(timezone.utc) + (settings.ACCESS_TOKEN_EXPIRATION if token_type == "access" else settings.REFRESH_TOKEN_EXPIRATION if token_type == "refresh" else settings.AUTH_FLOW_EXPIRATION)
    token = jwt.encode(
        {
            "user_id": user.id,
            "exp": expiry, 
            "type": token_type,
        },
        settings.TOKEN_SECRET,
        algorithm=settings.TOKEN_ALGORITHM
    )

    if token_type == "refresh":
        if RefreshToken.objects.all().filter(user=user).exists():
            RefreshToken.objects.all().filter(user=user).delete()
        RefreshToken(user=user, token=token, expires=expiry).save()

    if token_type == "authflow":
        if AuthToken.objects.all().filter(user=user).exists():
            AuthToken.objects.all().filter(user=user).delete()
        AuthToken(user=user, token=token, expires=expiry).save()

    return token


def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.TOKEN_SECRET,  
            algorithms=[settings.TOKEN_ALGORITHM] 
        )  
        user = User.objects.get(id=payload["user_id"])
        if payload["type"] == "refresh" and not RefreshToken.objects.all().filter(user=user).exists():
            return None
        elif payload["type"] == "authflow" and not AuthToken.objects.all().filter(user=user).exists():
            return None
        else:
            if payload["type"] == "authflow":
                AuthToken.objects.all().filter(user=user).delete()
            return {"user": user, "type": payload["type"]}
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except User.DoesNotExist:
        return None
