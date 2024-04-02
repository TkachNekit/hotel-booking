from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from validators import validate_telegram_id


class User(AbstractUser):
    first_name = models.CharField(max_length=128, blank=False, null=False)
    last_name = models.CharField(max_length=128, blank=False, null=False)
    username = models.CharField(max_length=128, blank=False, null=False, unique=True,
                                validators=[UnicodeUsernameValidator()])
    email = models.EmailField(blank=False, null=False, unique=True)


class TelegramAuthorization(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=False, null=False)
    telegram_id = models.PositiveIntegerField(null=False, blank=False, unique=True, validators=[validate_telegram_id])
    authorization_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} | Authorized on telegram account \"{self.telegram_id}\" | {self.authorization_date}"


class TelegramUser:
    def __init__(self, user: User):
        self.username = user.username
        self.first_name = user.first_name
        self.last_name = user.last_name
        self.email = user.email
        self.is_superuser = user.is_superuser
        self.last_login = user.last_login

    def __str__(self):
        return f"{self.username}"
