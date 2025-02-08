from django.db import models
from django.core.validators import RegexValidator

from api.constants import MAX_LENGTH, MAX_MEASURENENT_UNUT
from users.models import User


SLUG_MAX_LENGTH = 32
COOKING_TIME_MIN = 1
COOKING_TIME_MAX = 32000
AMOUNT_MIN = 1
AMOUNT_MAX = 32000


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT,
        verbose_name='Единица измерения'
    )

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        verbose_name='Название'
    )
    slug = models.CharField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        validators=[RegexValidator(r'^[-a-zA-Z0-9_]+$')],
        null=True,
        blank=True,
        verbose_name='Слаг'
    )
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение'
    )
    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Название'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(COOKING_TIME_MIN),
            MaxValueValidator(COOKING_TIME_MAX)
        ],
        verbose_name='Время приготовления'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        default=AMOUNT_MIN,
        blank=True,
        validators=[
            MinValueValidator(AMOUNT_MIN),
            MaxValueValidator(AMOUNT_MAX)
        ],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique ingredient')]


class ShoppingCart(models.Model):
    """Модель для списка покупок пользователя. """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_in_shopping_cart',
        verbose_name='Рецепт',

    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ['user', 'recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_user_recipe_in_cart'
            )
        ]

    def __str__(self):
        return f'{self.recipe.name} в списке покупок у {self.user.username}'


class Favorite(models.Model):
    """Модель для избранных рецептов пользователей."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_favorited',
        verbose_name='Рецепт'
    )
    created_at = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} добавил в избранное {self.recipe.name}'
