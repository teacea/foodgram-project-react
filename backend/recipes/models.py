
from django.core.validators import MinValueValidator
from django.db import models
from user.models import User


class Tag(models.Model):
    BLUE = '#0000FF'
    ORANGE = '#FFA500'
    GREEN = '#008000'
    PURPLE = '#800080'
    YELLOW = '#FFFF00'

    COLOR_CHOICES = [
        (BLUE, 'Синий'),
        (ORANGE, 'Оранжевый'),
        (GREEN, 'Зеленый'),
        (PURPLE, 'Фиолетовый'),
        (YELLOW, 'Желтый'),
    ]

    name = models.CharField(
        'Название тега',
        max_length=200
    )
    color = models.CharField(
        'Цвет',
        max_length=7,
        choices=COLOR_CHOICES
    )
    slug = models.SlugField(
        'Адрес',
        unique=True,
        max_length=200,
    )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=30,
        null=False
    )
    name = models.CharField(
        'Название ингредиента',
        max_length=40,
        null=False
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique ingredient')
        ]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='photo',
        blank=True,
        null=True,
        help_text='Загрузите фотографию'
    )
    description = models.TextField(
        'Описание процесса приготовления',
        max_length=1000,
        help_text='Напишите свой рецепт здесь,ограничение-1000 символов'
    )
    tag = models.ManyToManyField(
        Tag,
        verbose_name='Тег',
        related_name='recipes'

    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='QuanityRecepies',
        verbose_name='Ингредиенты',
        related_name='ingredients'
    )
    time = models.SmallIntegerField(
        'Время приготовления',
        max_length=10,
        validators=(
            MinValueValidator(
                1, message='Время должно быть больше 1 минуты'),)
    )
    name = models.CharField(
        'Название блюда',
        max_length=100)
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class QuanityRecepies(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='quanity'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='ингредиент',
        related_name='quanity')
    quanity = models.PositiveSmallIntegerField(
        blank=False,
        null=False,
        verbose_name='Количество ингредиента'
    )

    class Meta:
        constraints = (
                models.UniqueConstraint(
                    fields=('ingredient', 'recipe',),
                    name='unique ingredient quanity',
                ),
            )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites_user',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique favorite')
        ]


class ShoppingCart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='users_shoping_cart',
        verbose_name='владелец корзины'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='purchase',
        verbose_name='Покупка'
    )
