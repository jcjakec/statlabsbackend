from ninja import Router

from utils.schemas import ErrorOut, SuccessOut
from .schemas import UrlOut, UserSchema

from .models import Account
from services.users.models import User
from services.games.models import Platform

from django.conf import settings
from django.shortcuts import redirect
from authentication.utility import generate_token, decode_token

import requests
from urllib.parse import urlencode



# Main router
router = Router()

# External account linking
extacc_router = Router() # /api/users/accounts/
STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

# STEAM OPENID account links

# Link generator
@extacc_router.get("/steam", response={200: UrlOut, 400: ErrorOut})
def steam_link_url(request):
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": f"{settings.SITE_URL}/api/users/accounts/steam/callback/?state={generate_token(request.auth, "authflow")}",
        "openid.realm": settings.SITE_URL,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }
    redirect_url = f"{STEAM_OPENID_URL}?{urlencode(params)}"
    return {"url": redirect_url}  

# Callback Link
@extacc_router.get("/steam/callback", response = {400: ErrorOut}, auth=None)
def steam_callback(request):
    params = request.GET
    print(params)
    if params.get("state"):
        user = decode_token(params.get("state"))
        if not user or not user["user"] or user["type"] != "authflow":
            return 400, {"message": "User authentication failed."}
    else:
        return 400, {"message": "Unable to resolve state."}
    
    claimed_id = params.get("openid.claimed_id", "")
    steam_id = claimed_id.split("/")[-1] if "steamcommunity.com/openid/id/" in claimed_id else None
    print(steam_id)
    if not steam_id or not steam_id.isdigit() or len(steam_id) != 17:
        return 400,{"message": "Invalid steamid."}

    nparams = params.copy()
    nparams["openid.mode"] = "check_authentication"
    checkurl = f"{STEAM_OPENID_URL}?{urlencode(nparams)}"
    print(checkurl)
    response = requests.post(checkurl)   
    print(response.text) 
    if response.status_code != 200 or "is_valid:true" not in response.text:
        return 400, {"message": "Request invalidated by Steam."}

    platform= Platform.objects.get(name="Steam")
    Account.objects.update_or_create(user=user["user"], platform=platform, defaults={"uid": int(steam_id)})

    return redirect("/api/docs")



# User routes
@router.get("/{user_id}", response={200: UserSchema, 404: ErrorOut})
def user_by_id(request, user_id: int):
    try:
        user = User.objects.prefetch_related("accounts").get(id=user_id)
        return user
    except User.DoesNotExist:
        return 404, {"message": "User not found"}
