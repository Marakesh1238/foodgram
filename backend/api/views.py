import csv
from io import StringIO, BytesIO
from django.http import FileResponse
from .permissions import IsAuthenticatedOr401
from rest_framework.viewsets import ModelViewSet
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from .filters import RecipeFilter, IngredientFilter
from recipes.models import Favorite, Recipe, ShoppingCart, Tag, Ingredient
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeCreateSerializer,
                          RecipeShortSerializer, ShoppingCartSerializer,
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

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update',
                           'destroy', 'download_shopping_cart',
                           'manage_shopping_cart']:
            permission_classes = [IsAuthenticatedOr401]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

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

    @action(detail=False, methods=['get'], url_path='download_shopping_cart',
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)
        recipes = [item.recipe for item in shopping_cart if item.recipe]

        # Создание CSV файла
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Image', 'Cooking Time'])
        for recipe in recipes:
            writer.writerow([recipe.id, recipe.name,
                             recipe.image.url, recipe.cooking_time])

        output.seek(0)
        response = FileResponse(BytesIO(output.getvalue().encode('utf-8')), content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; '
            'filename="shopping_cart.csv"'
        )
        return response

    @action(detail=True, methods=['post', 'delete', 'get'], url_path='shopping_cart',
            permission_classes=[permissions.IsAuthenticated])
    def manage_shopping_cart(self, request, pk=None):
        user = request.user

        if request.method == 'GET':
            shopping_cart = ShoppingCart.objects.filter(user=user)
            serializer = ShoppingCartSerializer(shopping_cart, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({"detail": "Recipe not found."},
                            status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            shopping_cart, created = ShoppingCart.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                return Response({"detail": "Recipe already in shopping cart."},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(RecipeShortSerializer(recipe).data,
                            status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                shopping_cart = ShoppingCart.objects.get(user=user, recipe=recipe)
            except ShoppingCart.DoesNotExist:
                return Response({"detail": "Recipe not in shopping cart."},
                                status=status.HTTP_400_BAD_REQUEST)
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post', 'delete', 'get'], url_path='favorite',
            permission_classes=[permissions.IsAuthenticated])
    def manage_favorite(self, request, pk=None):
        user = request.user

        if request.method == 'GET':
            favorites = Favorite.objects.filter(user=user)
            serializer = FavoriteSerializer(favorites, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({"detail": "Recipe not found."},
                            status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                return Response({"detail": "Recipe already in favorites."},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(RecipeShortSerializer(recipe).data,
                            status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(user=user, recipe=recipe)
            except Favorite.DoesNotExist:
                return Response({"detail": "Recipe not in favorites."},
                                status=status.HTTP_400_BAD_REQUEST)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.author != request.user:
            raise PermissionDenied("You do not have permission to update this recipe.")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("You do not have permission to delete this recipe.")
        instance.delete()


class FavoriteViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='favorite')
    def add_to_favorite(self, request, pk=None):
        user = request.user
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)

        favorite, created = Favorite.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            return Response({"detail": "Recipe already in favorites."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(FavoriteSerializer(favorite).data, status=status.HTTP_201_CREATED)

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
