from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientDetailView, IngredientListView, RecipeViewSet,
                    TagListCreateView, TagRetrieveView, UserViewSet)

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
]


urlpatterns = [
    path('', include(router.urls)),
] + auth_urlpatterns + recipe_urlpatterns
