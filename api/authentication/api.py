from .utility import generate_token, decode_token
from .schemas import UserRegistration, UserLogin, TokensOut, ErrorOut, SuccessOut, RefreshIn
from .models import RefreshToken
from django.contrib.auth import authenticate
from ninja import Router
from services.users.models import User
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError



# OAuth Spec for JWT/token authentication
# This serves as the token management, auth.py determines access to resources
#  +--------+                                           +---------------+
#  |        |--(A)------- Authorization Grant --------->|               |
#  |        |                                           |               |
#  |        |<-(B)----------- Access Token -------------|               |
#  |        |               & Refresh Token             |               |
#  |        |                                           |               |
#  |        |                            +----------+   |               |
#  |        |--(C)---- Access Token ---->|          |   |               |
#  |        |                            |          |   |               |
#  |        |<-(D)- Protected Resource --| Resource |   | Authorization |
#  | Client |                            |  Server  |   |     Server    |
#  |        |--(E)---- Access Token ---->|          |   |               |
#  |        |                            |          |   |               |
#  |        |<-(F)- Invalid Token Error -|          |   |               |
#  |        |                            +----------+   |               |
#  |        |                                           |               |
#  |        |--(G)----------- Refresh Token ----------->|               |
#  |        |                                           |               |
#  |        |<-(H)----------- Access Token -------------|               |
#  +--------+           & Optional Refresh Token        +---------------+
# 
#  
#  (A)  The client requests an access token by authenticating with the
#       authorization server and presenting an authorization grant.
#  
#  (B)  The authorization server authenticates the client and validates
#       the authorization grant, and if valid, issues an access token
#       and a refresh token.
#  
#  (C)  The client makes a protected resource request to the resource
#       server by presenting the access token.
#  
#  (D)  The resource server validates the access token, and if valid,
#       serves the request.
#  
#  (E)  Steps (C) and (D) repeat until the access token expires.  If the
#       client knows the access token expired, it skips to step (G);
#       otherwise, it makes another protected resource request.
#  
#  (F)  Since the access token is invalid, the resource server returns
#       an invalid token error.
#  
#  (G)  The client requests a new access token by authenticating with
#       the authorization server and presenting the refresh token.  The
#       client authentication requirements are based on the client type
#       and on the authorization server policies.
#  
#  (H)  The authorization server authenticates the client and validates
#       the refresh token, and if valid, issues a new access token (and,
#       optionally, a new refresh token).



# Routers
auth_router = Router(tags=["Token Authentication"])
registration_router = Router(tags=["Registration"])

# Registration - returns access and refresh

@registration_router.post("/register", auth=None, response={201: TokensOut, 400: ErrorOut})
def register(request, details: UserRegistration):
    if details.password != details.confirm_password:
        return 400, {"message": "Passwords do not match"}

    if User.objects.all().filter(username=details.username):
        return 400, {"message": "Username already exists"}

    try:
        password_validation.validate_password(details.password)
    except ValidationError as e:
         return 400, {"message": e}
    
    user = User.objects.create_user(username=details.username, password=details.password, email=details.email)

    user = authenticate(username=details.username, password=details.password)
    access_token = generate_token(user, "access")
    refresh_token = generate_token(user, "refresh")
    return 201, {"access": access_token,
                "refresh": refresh_token}


# Login - returns access and refresh tokens
@auth_router.post("/login", auth=None, response={200: TokensOut, 400: ErrorOut})
def obtain_tokens(request, details: UserLogin):
    # authenticate user
    user = authenticate(username=details.username, password=details.password)
    if not user:
        return 400, {"message": "Invalid username or password"}
    
    access_token = generate_token(user, "access")
    refresh_token = generate_token(user, "refresh")

    return 200, {"access": access_token, 
                 "refresh": refresh_token}


# Refresh - for users to retrieve a new access token with their refresh token
@auth_router.post("/refresh", auth=None, response={200: TokensOut, 400: ErrorOut})
def refresh_token(request, details: RefreshIn):
    if not details.refresh:
        return 400, {"message": "Refresh token missing"}

    payload = decode_token(details.refresh)
    if payload["user"] and payload["type"] == "refresh":
        try:
            dbexists = RefreshToken.objects.get(token=details.refresh, user=payload['user'])
            new_access_token = generate_token(payload["user"], "access")
            return 200, {"access": new_access_token}
        except RefreshToken.DoesNotExist:
            return 400, {'message': 'Invalid refresh token'}
    else:
        return 400, {"message": "Invalid refresh token"}


# Logout

@auth_router.post("/logout", response={200: SuccessOut, 400: ErrorOut})
def invalidate_refresh_token(request):
    user = request.auth

    if user:
        if RefreshToken.objects.all().filter(user=user).exists():
            RefreshToken.objects.all().filter(user=user).delete()
        return 200, {"message": "Logged out"}
    else:
        return 400, {"message": "Invalid access token"}

    
