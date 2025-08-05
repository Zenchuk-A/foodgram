import django_filters
from recipes.models import Recipe


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 't', 'yes', 'y')
    return bool(value)


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = django_filters.NumberFilter(field_name='author__id')
    is_favorited = django_filters.CharFilter(
        method='filter_is_favorited',
    )
    is_in_shopping_cart = django_filters.CharFilter(
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        val = str_to_bool(value)
        print(f'filter_is_favorited value: {val} ({type(val)})')
        user = self.request.user
        if user.is_anonymous:
            return queryset.none() if val else queryset
        if val:
            return queryset.filter(favorited_by__user=user)
        return queryset.exclude(favorited_by__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        val = str_to_bool(value)
        print(f'filter_is_in_shopping_cart value: {val} ({type(val)})')
        user = self.request.user
        if user.is_anonymous:
            return queryset.none() if val else queryset
        if val:
            return queryset.filter(in_shopping_lists__user=user)
        return queryset.exclude(in_shopping_lists__user=user)
