from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet
from .views import (AddRecipeToShoppingListView, DownloadShoppingListView,
                    IngredientDetailView,
                    IngredientListView,
                    RecipeFavoritesView,
                    RecipeViewSet,
                    TagListCreateView,
                    TagRetrieveView)


router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register('users', UserViewSet, basename='users')


auth_urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]


recipe_urlpatterns = [
    path('', include(router.urls)),
    path("ingredients/", IngredientListView.as_view(),
         name="ingredient-list"),
    path(
        "ingredients/<int:id>/",
        IngredientDetailView.as_view(),
        name="ingredient-detail",
    ),
    path('tags/', TagListCreateView.as_view(),
         name='tag-list-create'),
    path('tags/<int:id>/', TagRetrieveView.as_view(),
         name='tag-retrieve'),
    path('recipes/<int:pk>/get-link/',
         RecipeViewSet.as_view({'get': 'get_link'}),
         name='recipe-get-link'),
    # Скачать список покупок.
    path(
        "recipes/download_shopping_cart/",
        DownloadShoppingListView.as_view(),
        name="download-shopping-list",
    ),
    # Добавить рецепт в список покупок. Удалить рецепт из списка покупок.
    path(
        "recipes/<int:id>/shopping_cart/",
        AddRecipeToShoppingListView.as_view(),
        name="add-recipe-to-shopping-list",
    ),
    # Добавить в избранное. Удалить из избранного.
    path(
        "recipes/<int:id>/favorite/",
        RecipeFavoritesView.as_view(),
        name="add-recipe-to-favorites",
    ),
]


urlpatterns = [
    path('', include(router.urls)),
] + auth_urlpatterns + recipe_urlpatterns
