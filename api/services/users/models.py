from django.db import models
from django.contrib.auth.models import AbstractUser
from services.games.models import Platform

class User(AbstractUser):
    pass

    def __str__(self):
        return self.username

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    uid = models.CharField(max_length=200, null=True, blank=True, unique=True)

    def __str__(self):
        return self.user.username + " - " + self.platform.name
