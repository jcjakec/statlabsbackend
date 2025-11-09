from django.contrib import admin
from .models import * 

# Register your models here.
admin.site.register(Game)
admin.site.register(Company)
admin.site.register(Platform)
admin.site.register(GameInstance)
admin.site.register(Tag)
