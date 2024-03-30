from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    first_name = models.CharField(max_length=128, blank=False, null=False)
    last_name = models.CharField(max_length=128, blank=False, null=False)
    username = models.CharField(max_length=128, blank=False, null=False, unique=True)
    email = models.CharField(max_length=256, blank=False, null=False, unique=True)


class TelegramAuthorization(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=False, null=False)
    telegram_id = models.IntegerField(null=False, blank=False, unique=True)
    authorization_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User {self.user.username} authorized on {self.telegram_id}"
