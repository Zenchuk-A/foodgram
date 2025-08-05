from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from .validators import forbidden_names_validator

USERNAME_MAX_LENGTH = 150
EMAIL_MAX_LENGTH = 150


class UserProfile(AbstractUser):
    email = models.EmailField(
        'Адрес электронной почты',
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
    )
    username = models.CharField(
        'Логин',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator(), forbidden_names_validator],
    )
    is_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField(
        upload_to='users/images/', null=True, default=None, blank=True
    )

    def __str__(self):
        return f'Пользователь: {self.username}'

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
