import uuid
from base64 import b64decode

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.serializers import (
    CharField,
    ImageField,
    ModelSerializer,
    ReadOnlyField,
    SerializerMethodField,
    ValidationError
)
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Recipe
from .models import Subscription, User


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
        user = User.objects.create_user(**validated_data)
        return user

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
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit', None)
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
