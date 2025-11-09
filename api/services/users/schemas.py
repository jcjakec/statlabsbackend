from ninja import ModelSchema, Schema
from .models import Account
from services.games.schemas import PlatformSchema

class UrlOut(Schema):
    url: str


class AccountSchema(Schema):
    platform: PlatformSchema
    uid: int

class UserSchema(Schema):
    id: int 
    username: str
    accounts: list[AccountSchema]