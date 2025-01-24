from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .permissions import IsAuthenticatedOr401
from .filters import RecipeFilter, IngredientFilter
from recipes.models import Favorite, Recipe, ShoppingCart, Tag, Ingredient
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeCreateSerializer,
                          ShoppingCartSerializer,
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
        if is_favorited is not None:
            is_favorited = is_favorited.lower() == 'true'
            queryset = queryset.filter(is_favorited=is_favorited)
        return queryset.order_by('id')

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


class DownloadShoppingListView(APIView):
    """Скачиваем файл со списком покупок."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        shopping_list = ShoppingCart.objects.filter(user=request.user)
        file_content = "\n".join([str(item) for item in shopping_list])
        response = Response(file_content, content_type="text/plain")
        response["Content-Disposition"] = \
            'attachment; filename="shopping_list.txt"'
        return response


class AddRecipeToShoppingListView(APIView):
    """Добавляем рецепт в список покупок."""

    permission_classes = [IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=id)
        data = {
            "user": request.user.id,
            "recipe": recipe.id,
        }
        serializer = ShoppingCartSerializer(
            data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id, *args, **kwargs):
        shopping_list_item = get_object_or_404(
            ShoppingCart, user=request.user, recipe__id=id
        )
        shopping_list_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeFavoritesView(APIView):
    """Добавляем рецепт в избранное."""

    permission_classes = [IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, recipe=recipe
        )

        if not created:
            return Response(
                {"detail": "Рецепт уже в избранном!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = FavoriteSerializer(favorite)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id, *args, **kwargs):
        favorite = get_object_or_404(
            Favorite, user=request.user, recipe_id=id)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
