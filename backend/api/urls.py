from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet
from .views import CustomTokenObtainPairView, FavoriteViewSet, IngredientViewSet, RecipeViewSet, ShoppingCartViewSet, TagViewSet


router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register('users', UserViewSet, basename='users')


auth_urlpatterns = [
    path('auth/token/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
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
]


urlpatterns = [
    path('', include(router.urls)),
] + auth_urlpatterns + recipe_urlpatterns
