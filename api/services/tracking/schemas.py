from ninja import Schema, ModelSchema
from .models import Stat, StatValue, Achievement, AchievementStatus, InstanceCompletion, GameCompletion
from datetime import datetime

# Statistic schemas
class FullStatSchema(ModelSchema):
    class Meta:
        model = Stat
        fields = "__all__"

class StatSchema(Schema):
    id: int
    name: str
    displayname: str
    
class StatValueSchema(ModelSchema):
    stat: StatSchema 

    class Meta:
        model = StatValue
        fields = "__all__"


# Achievement schemas
class FullAchievementSchema(ModelSchema):
    class Meta:
        model = Achievement
        fields = "__all__"
    
class AchievementSchema(Schema):
    id: int
    name: str
    displayname: str
    icon: str

class AchievementStatusSchema(ModelSchema):
    achievement: AchievementSchema 

    class Meta:
        model = AchievementStatus
        fields = "__all__"


# Completion Schemas
class CompletionSchema(Schema):
    percentage: float
    refresh: datetime = None
