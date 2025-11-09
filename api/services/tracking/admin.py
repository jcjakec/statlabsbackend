from django.contrib import admin
from .models import Stat, StatValue, Achievement, AchievementStatus

# Register your models here.
admin.site.register(Stat)
admin.site.register(StatValue)
admin.site.register(Achievement)
admin.site.register(AchievementStatus)
