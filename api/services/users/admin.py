from django.contrib import admin
from .models import User, Account   

# Register your models here.
admin.site.register(User)
admin.site.register(Account)