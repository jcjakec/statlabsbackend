from ninja import Schema

# Registration
class UserRegistration(Schema):
    username: str
    email: str
    password: str
    confirm_password: str

class UserLogin(Schema):
    username: str
    password: str

class RefreshIn(Schema):
    refresh: str


class TokensOut(Schema):
    access: str
    refresh: str = None


class ErrorOut(Schema):
    message: str

class SuccessOut(Schema):
    message: str

