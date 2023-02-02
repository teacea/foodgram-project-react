from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    ROLE_CHOICES = [
        (USER, 'Авторизированный пользователь'),
        (MODERATOR, 'Модератор'),
        (ADMIN, 'Администратор'),
    ]
    username = models.TextField(
        'имя пользователя',
        blank=True,
        unique=True
    )
    first_name = models.TextField(
        'Имя пользователя',
        blank=True)
    last_name = models.TextField(
        'Фамилия',
        blank=True)
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
    )
    bio = models.TextField(
        'Биография',
        blank=True,
    )

    role = models.CharField(
        "Пользовательские роли",
        choices=ROLE_CHOICES,
        default=USER,
        max_length=15,
    )


class VerificationEmailKey(models.Model):
    """Модель ключей подтверждения."""
    key = models.CharField(
        verbose_name='Key',
        max_length=64,
        primary_key=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification',
    )


class Follow(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Объект подписки'
    )

    class Meta:
        ordering = ['author']
        verbose_name = 'подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'], name='follow')
        ]

    def __str__(self):
        return self.text[:15]
