from django.contrib import admin

from .models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    Follow,
    ShoppingList,
    RecipeTag,
    IngredientRecipe,
    ShortLink,
)


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag
    extra = 0
    min_num = 1


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    fields = (
        'ingredient',
        'amount',
    )
    extra = 0
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (
        RecipeTagInline,
        IngredientRecipeInline,
    )
    list_display = (
        'name',
        'author_name',
    )
    search_fields = (
        'name',
        'author__username',
    )
    list_filter = ('tags',)

    def author_name(self, obj):
        return obj.author.first_name or obj.author.username

    author_name.admin_order_field = 'author__first_name'
    author_name.short_description = 'Автор'

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


class ShortLinkAdmin(admin.ModelAdmin):
    list_display = (
        'recipe_id',
        'recipe',
        'short_url',
    )
    readonly_fields = ('recipe', 'short_url')
    search_fields = ('recipe__name',)

    class Meta:
        model = ShortLink
        fields = (
            'recipe',
            'short_url',
        )


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingList, ShoppingListAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(ShortLink, ShortLinkAdmin)
