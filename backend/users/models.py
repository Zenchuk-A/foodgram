from django.contrib.auth.models import AbstractUser
from django.db import models

FIRST_NAME_MAX_LENGTH = 150
LAST_NAME_MAX_LENGTH = 150


class UserProfile(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(
        'Адрес электронной почты',
        unique=True,
    )
    first_name = models.CharField(
        'Имя', blank=False, null=False, max_length=FIRST_NAME_MAX_LENGTH
    )
    last_name = models.CharField(
        'Фамилия', blank=False, null=False, max_length=LAST_NAME_MAX_LENGTH
    )
    avatar = models.ImageField(
        upload_to='users/images/', null=True, default=None, blank=True
    )

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Пользователь: {self.username}'
