from django.db import models
from django.core.validators import RegexValidator

from api.constants import MAX_LENGTH, MAX_MEASURENENT_UNUT
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_LENGTH)
    measurement_unit = models.CharField(max_length=MAX_MEASURENENT_UNUT)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True)
    slug = models.CharField(
        max_length=32,
        unique=True,
        validators=[RegexValidator(r'^[-a-zA-Z0-9_]+$')],
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='recipes')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient')
    tags = models.ManyToManyField(Tag, related_name='tags')
    image = models.ImageField(upload_to='recipes/images/')
    name = models.CharField(max_length=MAX_LENGTH)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=1, blank=True)

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
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_favorited',
        verbose_name='Рецепт',
    )
    created_at = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
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
