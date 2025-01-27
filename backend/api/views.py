from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from collections import defaultdict
from django.http import HttpResponse
from .pagination import LimitPageNumberPagination

from .permissions import IsAuthenticatedOr401
from .filters import RecipeFilter, IngredientFilter
from recipes.models import Favorite, Recipe, ShoppingCart, Tag, Ingredient
from .serializers import (IngredientSerializer,
                          RecipeSerializer, RecipeCreateSerializer,
                          TagSerializer)


class IngredientListView(generics.ListAPIView):
    """
    Получаем список ингредиентов с возможностью поиска по имени.
    """

    serializer_class = IngredientSerializer

    def get_queryset(self):
        name = self.request.query_params.get("name", None)
        queryset = Ingredient.objects.all()
        if name:
            queryset = queryset.filter(name__startswith=name)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class IngredientDetailView(generics.RetrieveAPIView):
    """Получаем ингредиент по его ID."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    lookup_field = "id"
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filterset_class = RecipeFilter
    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update',
                           'destroy', 'download_shopping_cart']:
            permission_classes = [IsAuthenticatedOr401]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # Применяем сортировку
        queryset = queryset.order_by('id')

        if user.is_authenticated:
            # Получаем параметры фильтрации из запроса
            is_favorited = self.request.query_params.get('is_favorited')
            is_in_shopping_cart = self.request.query_params.get(
                'is_in_shopping_cart')
            # Фильтрация по избранному
            if is_favorited is not None:
                if is_favorited == '1':
                    queryset = queryset.filter(is_favorited__user=user)
                elif is_favorited == '0':
                    queryset = queryset.exclude(is_favorited__user=user)
            # Фильтрация по корзине
            if is_in_shopping_cart is not None:
                if is_in_shopping_cart == '1':
                    queryset = queryset.filter(is_in_shopping_cart__user=user)
                elif is_in_shopping_cart == '0':
                    queryset = queryset.exclude(is_in_shopping_cart__user=user)

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Получаем список рецептов с возможностью фильтрации.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)

        if request.method == 'POST':  # Add to favorites
            if favorite.exists():
                return Response({"error": "Recipe already in favorites"},
                                status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response({
                "id": recipe.id,
                "name": recipe.name,
                "image": recipe.image.url if recipe.image else None,
                "cooking_time": recipe.cooking_time
            }, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not favorite.exists():
                return Response({"error": "Recipe not in favorites"},
                                status=status.HTTP_400_BAD_REQUEST)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        # Получаем все рецепты из списка покупок пользователя
        shopping_cart = ShoppingCart.objects.filter(user=request.user)

        # Создаем словарь для хранения ингредиентов и их количества
        ingredients = defaultdict(int)

        # Собираем ингредиенты из рецептов
        for cart_item in shopping_cart:
            for recipe_ingredient in cart_item.recipe.recipeingredient_set.all():
                ingredient = recipe_ingredient.ingredient
                ingredients[ingredient.name] += recipe_ingredient.amount

        # Формируем текстовый файл
        lines = [
            f"{name} — {amount}\n" for name, amount in ingredients.items()
        ]
        response = HttpResponse("".join(lines), content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        cart_item = ShoppingCart.objects.filter(user=request.user,
                                                recipe=recipe)

        if request.method == 'POST':  # Add to shopping cart
            if cart_item.exists():
                return Response({"error": "Recipe already in shopping cart"},
                                status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            return Response({
                "id": recipe.id,
                "name": recipe.name,
                "image": recipe.image.url,
                "cooking_time": recipe.cooking_time
            }, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not cart_item.exists():
                return Response({"error": "Recipe not in shopping cart"},
                                status=status.HTTP_400_BAD_REQUEST)
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = f"https://{request.get_host()}/recipes/{recipe.id}"
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.author != request.user:
            raise PermissionDenied(
                "You do not have permission to update this recipe.")
        serializer = self.get_serializer(instance,
                                         data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied(
                "You do not have permission to delete this recipe.")
        instance.delete()


class TagListCreateView(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TagRetrieveView(generics.RetrieveAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'id'
