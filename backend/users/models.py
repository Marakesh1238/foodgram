from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)
    username_validator = RegexValidator(regex=r'^[\w.@+-]+\Z',
                                        message="Username must match the pattern ^[\w.@+-]+\Z")
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=150)
    is_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
