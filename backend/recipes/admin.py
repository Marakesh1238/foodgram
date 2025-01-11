from django.contrib import admin
from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag


class RecipeAdmin(admin.ModelAdmin):
    search_fields = ['title', 'author__username']
    list_filter = ['tags']


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ['name']


class ShoppingCartAdmin(admin.ModelAdmin):
    search_fields = ['user__username', 'recipe__title']


class FavoritesAdmin(admin.ModelAdmin):
    search_fields = ['user__username', 'recipe__title']


admin.site.register(Favorite, FavoritesAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
