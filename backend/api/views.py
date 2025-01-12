import csv
from io import StringIO
from django.http import FileResponse
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

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


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = []
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        author = self.request.query_params.get('author')
        tags = self.request.query_params.getlist('tags')

        if is_favorited is not None:
            queryset = queryset.filter(is_favorited=is_favorited)
        if is_in_shopping_cart is not None:
            queryset = queryset.filter(is_in_shopping_cart=is_in_shopping_cart)
        if author is not None:
            queryset = queryset.filter(author__id=author)
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        return queryset

    @action(detail=True, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = f"https://{request.get_host()}/recipes/{recipe.id}"
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


class ShoppingCartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.get(user=user)
        recipes = shopping_cart.recipes.all()

        # Создание CSV файла
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Image', 'Cooking Time'])
        for recipe in recipes:
            writer.writerow([recipe.id, recipe.name,
                             recipe.image.url, recipe.cooking_time])

        output.seek(0)
        response = FileResponse(output, content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.csv"')
        return response

    @action(detail=True, methods=['post'], url_path='shopping_cart')
    def add_to_shopping_cart(self, request, pk=None):
        user = request.user
        recipe = Recipe.objects.get(pk=pk)
        shopping_cart, created = ShoppingCart.objects.get_or_create(user=user)
        if recipe in shopping_cart.recipes.all():
            return Response({"detail": "Recipe already in shopping cart."},
                            status=status.HTTP_400_BAD_REQUEST)
        shopping_cart.recipes.add(recipe)
        return Response(RecipeSerializer(recipe).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='shopping_cart')
    def remove_from_shopping_cart(self, request, pk=None):
        user = request.user
        recipe = Recipe.objects.get(pk=pk)
        shopping_cart = ShoppingCart.objects.get(user=user)
        if recipe not in shopping_cart.recipes.all():
            return Response({"detail": "Recipe not in shopping cart."},
                            status=status.HTTP_400_BAD_REQUEST)
        shopping_cart.recipes.remove(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='favorite')
    def add_to_favorite(self, request, pk=None):
        user = request.user
        recipe = Recipe.objects.get(pk=pk)
        favorite, created = Favorite.objects.get_or_create(user=user,
                                                           recipe=recipe)
        if not created:
            return Response({"detail": "Recipe already in favorites."},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(RecipeSerializer(recipe).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='favorite')
    def remove_from_favorite(self, request, pk=None):
        user = request.user
        recipe = Recipe.objects.get(pk=pk)
        try:
            favorite = Favorite.objects.get(user=user, recipe=recipe)
            favorite.delete()
        except Favorite.DoesNotExist:
            return Response({"detail": "Recipe not in favorites."},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
