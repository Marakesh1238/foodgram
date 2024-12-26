from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FavoriteViewSet, RecipeViewSet, ShoppingCartViewSet


router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')


auth_urlpatterns = [
    path('', include('djoser.urls')),
    path("auth/", include("djoser.urls.authtoken")),
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
]


urlpatterns = [
    path('', include('users.urls')),
] + auth_urlpatterns + recipe_urlpatterns
