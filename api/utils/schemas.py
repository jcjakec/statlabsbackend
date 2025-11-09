from ninja import Schema

class ErrorOut(Schema):
    message: str

class SuccessOut(Schema):
    message: str

