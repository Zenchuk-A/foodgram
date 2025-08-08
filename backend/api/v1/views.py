from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingList,
    Tag,
)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeShortSerializer,
    SubscriptionSerializer,
    FollowSerializer,
    TagSerializer,
    UserProfileSerializer,
    AvatarSerializer,
    ShoppingListSerializer,
    FavoriteSerializer,
)
from .paginators import PageSizeLimitPagination

User = get_user_model()


@action(['get'], detail=False)
def redirect_to_recipe(request, short_url):
    """The function implements redirection
    from a short recipe link to the recipe page
    """
    recipe = get_object_or_404(Recipe, short_url=short_url)
    full_link = request.build_absolute_uri(f'/recipes/{recipe.id}/')
    return HttpResponseRedirect(full_link)


class ProfileViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PageSizeLimitPagination

    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()

    @action(["put"], detail=False, url_path='me/avatar')
    def avatar_upload(self, request, *args, **kwargs):
        user = request.user
        serializer = AvatarSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = serializer.save(user)
            return Response(
                {"avatar": request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    @avatar_upload.mapping.delete
    def avatar_delete(self, request, *args, **kwargs):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        page = self.paginate_queryset(queryset)
        recipes_limit = request.query_params.get('recipes_limit')
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit},
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)

        serializer = FollowSerializer(
            data={'following': author.id}, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)

        recipes_limit = request.query_params.get('recipes_limit')
        response_serializer = SubscriptionSerializer(
            author,
            context={
                'request': request,
                'recipes_limit': recipes_limit,
            },
        )
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)

        deleted_count, _ = Follow.objects.filter(
            user=user, following=author
        ).delete()

        if not deleted_count:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filterset_class = IngredientFilter
    filter_backends = [DjangoFilterBackend]


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related(
        'tags', 'recipe_ingredients__ingredient', 'author'
    )
    permission_classes = [IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly]
    pagination_class = PageSizeLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'])
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        if not recipe.short_url:
            recipe.save()
        full_short_link = request.build_absolute_uri(f'/s/{recipe.short_url}/')
        return Response(
            {'short-link': full_short_link}, status=status.HTTP_200_OK
        )

    @action(
        detail=True, methods=['post'], permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление рецепта в избранное."""
        recipe = self.get_object()
        serializer = FavoriteSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = RecipeShortSerializer(
            recipe, context={'request': request}
        )
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаление рецепта из избранного."""
        recipe = self.get_object()
        deleted_count, _ = Favorite.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response(
                {'errors': 'Рецепт не был в избранном'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        """Добавление рецепта в корзину покупок."""
        recipe = self.get_object()
        serializer = ShoppingListSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаление рецепта из корзины покупок."""
        recipe = self.get_object()
        deleted_count, _ = ShoppingList.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response(
                {'errors': 'Рецепта нет в корзине покупок'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(in_shopping_lists__user=request.user)
        ingredients = (
            IngredientRecipe.objects.filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        lines = [
            f"{item['ingredient__name']} "
            f"({item['ingredient__measurement_unit']})"
            f" — {item['total_amount']}"
            for item in ingredients
        ]

        response = HttpResponse(
            "\n".join(lines), content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
