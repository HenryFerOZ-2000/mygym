from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class LoginAttempt(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    window_start = models.DateTimeField()
    failures = models.PositiveIntegerField(default=0)
