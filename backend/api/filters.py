import django_filters
import django_filters as filters
from django.core.exceptions import ValidationError

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag


class TagsMultipleChoiceField(
        filters.fields.MultipleChoiceField):
    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'],
                code='required')
        for val in value:
            if val in self.choices and not self.valid_value(val):
                raise ValidationError(
                    self.error_messages['invalid_choice'],
                    code='invalid_choice',
                    params={'value': val},)


class TagsFilter(filters.AllValuesMultipleFilter):
    field_class = TagsMultipleChoiceField


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_in_shopping_cart = django_filters.CharFilter(
        method='filter_is_in_shopping_cart')
    is_favorited = django_filters.CharFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset
        favorite_recipes = Favorite.objects.filter(
            user=user).values_list('recipe', flat=True)
        if value:
            return queryset.filter(id__in=favorite_recipes)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset
        shopping_cart_recipes = ShoppingCart.objects.filter(
            user=user).values_list('recipe', flat=True)
        if value:
            return queryset.filter(id__in=shopping_cart_recipes)
        return queryset
