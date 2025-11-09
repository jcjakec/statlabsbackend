from django.db import models
from datetime import datetime, timezone
from services.users.models import User
    
# Create your models here.
class RefreshToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.TextField(unique=True)
    expires = models.DateTimeField()

    def __str__(self):
        return self.token
    
    def expired(self):
        if datetime.now(timezone.utc) > self.expires:
            return True
        return False

class AuthToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.TextField(unique=True)
    expires = models.DateTimeField()

    def __str__(self):
        return self.token
    
    def expired(self):
        if datetime.now(timezone.utc) > self.expires:
            return True
        return False