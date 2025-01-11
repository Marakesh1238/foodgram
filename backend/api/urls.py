from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet
from .views import (FavoriteViewSet, IngredientDetailView, IngredientListView,
                    RecipeViewSet, ShoppingCartViewSet, TagViewSet)


router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'tags', TagViewSet, basename='tag')
router.register('users', UserViewSet, basename='users')


auth_urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]


recipe_urlpatterns = [
    path('', include(router.urls)),
    path('recipes/<int:pk>/shopping_cart/',
         ShoppingCartViewSet.as_view({
             'post': 'add_to_shopping_cart',
             'delete': 'remove_from_shopping_cart'
         }),
         name='recipe-shopping-cart'),
    path('recipes/download_shopping_cart/',
         ShoppingCartViewSet.as_view({
             'get': 'download_shopping_cart'
         }),
         name='download-shopping-cart'),
    path('recipes/<int:pk>/favorite/',
         FavoriteViewSet.as_view({
             'post': 'add_to_favorite',
             'delete': 'remove_from_favorite'
         }),
         name='recipe-favorite'),
    path("ingredients/", IngredientListView.as_view(),
         name="ingredient-list"),
    # Получение ингредиента по ID.
    path(
        "ingredients/<int:id>/",
        IngredientDetailView.as_view(),
        name="ingredient-detail",
    ),
]


urlpatterns = [
    path('', include(router.urls)),
] + auth_urlpatterns + recipe_urlpatterns
