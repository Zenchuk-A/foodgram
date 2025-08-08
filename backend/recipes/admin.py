from django.contrib import admin

from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingList,
    Tag,
)


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    fields = (
        'ingredient',
        'amount',
    )
    extra = 0
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientRecipeInline,)
    list_display = (
        'name',
        'author_name',
        'favorites_count',
    )
    search_fields = (
        'name',
        'author__username',
    )
    list_filter = ('tags',)
    readonly_fields = ('favorites_count',)

    def author_name(self, obj):
        return obj.author.first_name or obj.author.username

    author_name.admin_order_field = 'author__first_name'
    author_name.short_description = 'Автор'

    def favorites_count(self, obj):
        return obj.favorited_by.count()

    favorites_count.short_description = 'В избранном'
    favorites_count.admin_order_field = 'favorited_by__count'

    class Meta:
        model = Recipe
        fields = (
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
        )


class TagAdmin(admin.ModelAdmin):
    search_fields = ('name', 'slug')

    class Meta:
        model = Tag
        fields = (
            'name',
            'slug',
        )


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name',)

    class Meta:
        model = Ingredient
        fields = (
            'name',
            'measurement_unit',
        )


class FavoriteAdmin(admin.ModelAdmin):
    class Meta:
        model = Favorite
        fields = (
            'user',
            'recipe',
        )


class ShoppingListAdmin(admin.ModelAdmin):
    search_fields = (
        'user__username',
        'recipe__name',
    )

    class Meta:
        model = ShoppingList
        fields = (
            'user',
            'recipe',
        )


class FollowAdmin(admin.ModelAdmin):
    class Meta:
        model = Follow
        fields = (
            'user',
            'author',
        )


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingList, ShoppingListAdmin)
admin.site.register(Follow, FollowAdmin)
