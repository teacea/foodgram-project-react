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

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=100
    )
    name = models.CharField(
        'Название ингредиента',
        max_length=40,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique ingredient')
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipe',
        help_text='Загрузите фотографию'
    )
    text = models.TextField(
        'Описание процесса приготовления',
        max_length=1000,
        help_text='Напишите свой рецепт здесь,ограничение-1000 символов'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег',
        related_name='recipes'

    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientAmount',
        verbose_name='Ингредиенты',
        related_name='ingredients'
    )
    cooking_time = models.SmallIntegerField(
        'Время приготовления',
        #5 дней=7200 мин, этого вполне достаточно для приговления
        max_length=4,
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
        return f'Автор: {self.author.username} рецепт: {self.name}'


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='ингредиент',
        related_name='quanity')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        validators=[
            MinValueValidator(1, message='Минимальное значение 1')
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return (f'В рецепте {self.recipe.name} {self.amount} '
                f'{self.ingredient.measurement_unit} {self.ingredient.name}')


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique favourite')]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        ordering = ('id',)

    def __str__(self):
        return (f'Пользователь: {self.user.username}'
                f'рецепт: {self.recipe.name}')


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='users_shoping_cart',
        verbose_name='владелец корзины'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='purchase',
        verbose_name='Покупка'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique cart')]

    def __str__(self):
        return (f'Пользователь: {self.user.username},'
                f'рецепт в списке: {self.recipe.name}')
