from rest_framework import serializers

from users.serializers import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredient,
                            ShoppingCart, Tag)
from users.serializers import UserSerializer


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
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipeingredient_set')
    is_favorited = serializers.BooleanField(default=False, read_only=True)
    in_shopping_cart = serializers.SerializerMethodField(
        default=False, read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return obj.shopping_carts.filter(user=request.user).exists()


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
    image = Base64ImageField(required=False)

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

    def _validate_ingredients(self, ingredients):
        if not isinstance(ingredients, list) or not ingredients:
            raise serializers.ValidationError(
                "Ингредиенты обязательны и должны быть списком."
            )
        for ingredient in ingredients:
            if "id" not in ingredient or "amount" not in ingredient:
                raise serializers.ValidationError(
                    "Каждый ингредиент должен содержать id и количество."
                )

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
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.save()

        instance.tags.set(tags_data)

        instance.ingredients.clear()
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=instance, **ingredient_data)

        return instance

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipes = RecipeSerializer(many=True)

    class Meta:
        model = ShoppingCart
        fields = ['recipes']


class FavoriteSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer()

    class Meta:
        model = Favorite
        fields = ['recipe']
