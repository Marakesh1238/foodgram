from rest_framework import serializers

from users.serializers import Base64ImageField, UserRecipesSerializer
from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    author = UserRecipesSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipeingredient_set')
    is_favorited = serializers.BooleanField(default=False, read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(
        default=False, read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return obj.in_shopping_cart.filter(user=request.user).exists()


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ["id", "name", "measurement_unit", "amount"]


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
            'image',]

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Ingredients field cannot be empty.")

        ingredient_ids = [ingredient['id'] for ingredient in value]
        if not Ingredient.objects.filter(
                id__in=ingredient_ids).count() == len(ingredient_ids):
            raise serializers.ValidationError(
                "One or more ingredients do not exist.")

        for ingredient in value:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    (
                        f"Количество ингредиента {ingredient['id']} "
                        f"должно быть не меньше 1."
                    )
                )

        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError("Tags field cannot be empty.")
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Tags field contains duplicate tags.")
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Image field cannot be empty.")
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Cooking time must be at least 1 minute.")
        return value

    def update_ingredients(self, ingredients, recipe):
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        self.create_ingredients(ingredients, recipe)

    def create_ingredients(self, ingredients, recipe):
        for ingredient_data in ingredients:
            print(ingredient_data)
            ingredient_id = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_id,
                amount=amount,
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        instance.tags.set(tags)
        self.update_ingredients(ingredients, instance)

        return instance

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingList."""

    class Meta:
        model = ShoppingCart
        fields = ["id", "user", "recipe"]


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingCart."""

    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ["id", "user", "recipe"]

    def validate(self, data):
        """Проверяем, что рецепт ещё не в списке покупок пользователя."""
        user = self.context["request"].user
        recipe = data["recipe"]
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже в списке покупок!")
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Favorite.
    Добавляем рецепты в избранное и получаем информацию об избранном рецепте.
    """

    id = serializers.ReadOnlyField(source="recipe.id")
    name = serializers.ReadOnlyField(source="recipe.name")
    image = serializers.ImageField(source="recipe.image", read_only=True)
    cooking_time = serializers.ReadOnlyField(source="recipe.cooking_time")

    class Meta:
        model = Favorite
        fields = ["id", "name", "image", "cooking_time"]
