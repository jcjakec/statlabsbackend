from .models import Platform, Company, Tag
from ninja import ModelSchema, Schema

# Tag Schema
class TagSchema(ModelSchema):
    class Meta:
        model = Tag
        fields = ["id","name"]


# Company Schema
class CompanySchema(ModelSchema):
    class Meta:
        model = Company
        fields = ["id","name"]


# Platform Schema
class PlatformSchema(ModelSchema):
    class Meta:
        model = Platform
        fields = "__all__"


# PlatformProfile Schema
class GameInstanceSchema(Schema):
    id: int
    platform: PlatformSchema  
    uid: str
    url: str

# Game Schema
class GameSchema(Schema):
    id: int
    name: str
    description: str
    aliases: list[str]
    popularity: float
    cover: str
    companies: list[CompanySchema] 
    tags: list[TagSchema] 
    game_instances: list[GameInstanceSchema]  
