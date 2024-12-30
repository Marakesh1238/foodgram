from django.db import models
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(max_length=256)
    measurement_unit = models.CharField(max_length=20)

    def __str__(self):        
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=256)
    color = models.CharField(max_length=7)
    slug = models.SlugField(unique=True)


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='author')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient')
    tags = models.ManyToManyField(Tag, related_name='tags')
    image = models.ImageField(upload_to='recipes/images/')
    name = models.CharField(max_length=256)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.ingredient.name} for {self.recipe.name}"


class ShoppingCart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    recipes = models.ManyToManyField(Recipe, related_name='shopping_carts')


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'recipe')


class Subscription(models.Model):
    user = models.ForeignKey(User,
                             related_name='subscriptions',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User,
                               related_name='followers',
                               on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'author')