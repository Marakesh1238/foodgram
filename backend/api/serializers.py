import uuid
from base64 import b64decode

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.serializers import (
    CharField,
    ImageField,
    ModelSerializer,
    ReadOnlyField,
    SerializerMethodField,
    ValidationError
)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription, User


AMOUNT_MIN = 1
AMOUNT_MAX = 32000


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
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(AMOUNT_MIN),
            MaxValueValidator(AMOUNT_MAX)
        ]
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    author = UserRecipesSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipeingredient_set')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'tags', 'ingredients', 'image', 'name',
            'text', 'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        ]

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.is_favorited.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.is_in_shopping_cart.filter(user=user).exists()
        return False


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
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(COOKING_TIME_MIN),
            MaxValueValidator(COOKING_TIME_MAX)
        ]
    )

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
            'image', ]

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Ingredients field cannot be empty.')

        ingredient_ids = [ingredient['id'] for ingredient in value]
        if not Ingredient.objects.filter(
                id__in=ingredient_ids).count() == len(ingredient_ids):
            raise serializers.ValidationError(
                'One or more ingredients do not exist.')

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ingredients field contains duplicate ingredients.')

        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Tags field cannot be empty.')
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Tags field contains duplicate tags.')
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Image field cannot be empty.')
        return value

    def update_ingredients(self, ingredients, recipe):
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        self.create_ingredients(ingredients, recipe)

    def create_ingredients(self, ingredients, recipe):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data.get("id"),
                amount=ingredient_data.get("amount")
            ) for ingredient_data in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

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
        fields = ['id', 'user', 'recipe']


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, attrs):
        if ShoppingCart.objects.filter(user=attrs['user'],
                                       recipe=attrs['recipe']).exists():
            raise serializers.ValidationError('Рецепт уже в корзине.')
        return attrs


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Favorite.
    Добавляем рецепты в избранное и получаем информацию об избранном рецепте.
    """

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ['id', 'name', 'image', 'cooking_time']


class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            unique_filename = f'{uuid.uuid4()}.{ext}'
            data = ContentFile(b64decode(imgstr), name=unique_filename)
        return super().to_internal_value(data)


class UserRepresentationSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
        )


class UserCreateSerializer(UserCreateSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def validate(self, data):
        if data.get('username') == 'me':
            raise ValidationError(
                'Использовать имя me запрещено'
            )
        if User.objects.filter(username=data.get('username')):
            raise ValidationError(
                'Пользователь с таким username уже существует'
            )
        if User.objects.filter(email=data.get('email')):
            raise ValidationError(
                'Пользователь с таким email уже существует'
            )
        return data

    def create(self, validated_data): 
        return User.objects.create_user(**validated_data)

    def to_representation(self, instance):
        serializer = UserRepresentationSerializer(instance)
        return serializer.data


class UserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)
    avatar = Base64ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, object):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return object.following.filter(follower=request.user).exists()


class AvatarSerializer(ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionRecipeShortSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionShowSerializer(UserSerializer):

    recipes = SerializerMethodField()
    recipes_count = ReadOnlyField(source='recipes.count')

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'avatar',
            'recipes_count',
        )

    def get_recipes(self, object):
        recipes_limit = self.context['request'].query_params.get('recipes_limit', None)
        author_recipes = object.recipes.all()
        if recipes_limit is not None:
            author_recipes = object.recipes.all()[:int(recipes_limit)]
        return SubscriptionRecipeShortSerializer(
            author_recipes, many=True
        ).data


class SubscriptionSerializer(ModelSerializer):

    class Meta:
        model = Subscription
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('follower', 'following'),
                message='Вы уже подписывались на этого автора'
            )
        ]

    def validate(self, data):
        """Проверяем, что пользователь не подписывается на самого себя."""
        if data['following'] == data['follower']:
            raise ValidationError(
                'Подписка на cамого себя не имеет смысла'
            )
        return data

    def to_representation(self, instance):
        return SubscriptionShowSerializer(instance.author,
                                          context=self.context).data


class UserRecipesSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name',
                  'last_name', 'email', 'avatar', 'is_subscribed']
