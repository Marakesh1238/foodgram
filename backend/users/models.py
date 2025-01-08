from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

from api.constants import (HELP_TEXT_NAME, MAX_EMAIL_FIELD,
                           MAX_NAME_FIELD, UNIQUE_FIELDS)


class User(AbstractUser):
    email = models.EmailField(max_length=MAX_EMAIL_FIELD, unique=True)
    username_validator = RegexValidator(
        regex=r'^[\w.@+-]+\Z',
        message=HELP_TEXT_NAME)
    username = models.CharField(
        max_length=MAX_NAME_FIELD,
        unique=True,
        validators=[username_validator],
        error_messages=UNIQUE_FIELDS,
    )
    first_name = models.CharField(max_length=MAX_NAME_FIELD)
    last_name = models.CharField(max_length=MAX_NAME_FIELD)
    is_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    follower = models.ForeignKey(User,
                                 on_delete=models.CASCADE,
                                 related_name='follower',
                                 verbose_name='подписчик')
    following = models.ForeignKey(User,
                                  on_delete=models.CASCADE,
                                  related_name='following',
                                  verbose_name='Автор')

    class Meta:
        ordering = ('id',)
        constraints = (
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='unique_subscription'
            ),
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.follower.username} подписан {self.following.username}'
