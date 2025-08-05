import base64
import imghdr
import uuid

from django.core.files.base import ContentFile
from django.http import Http404, HttpResponse
from rest_framework import viewsets, status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from djoser.views import UserViewSet
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Sum

from .serializers import (
    UserProfileSerializer,
    SetPasswordSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    SubscriptionSerializer,
)
from .permissions import IsAuthorOrReadOnly
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    ShortLink,
    Favorite,
    Follow,
    ShoppingList,
    IngredientRecipe,
)
from .filters import RecipeFilter

User = get_user_model()


@action(['get'], detail=False)
def redirect_to_recipe(request, short_url):
    short_link = get_object_or_404(ShortLink, short_url=short_url)
    full_link = request.build_absolute_uri(f'/recipes/{short_link.recipe.id}/')
    return redirect(full_link)


class CustomTokenCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {"error": "Email и пароль обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response(
                    {"error": "Неверные учетные данные"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {"auth_token": token.key},
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            return Response(
                {"error": "Неверные учетные данные"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CustomTokenLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except (AttributeError, ObjectDoesNotExist):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 6
    max_page_size = 100


class ProfileViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        paginator = PageNumberPagination()
        limit = request.query_params.get('limit')
        if limit and limit.isdigit():
            paginator.page_size = int(limit)
        else:
            paginator.page_size = 10

        page = paginator.paginate_queryset(self.queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_data = {
            "email": user.email,
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        user = request.user
        avatar_url = (
            request.build_absolute_uri(user.avatar.url)
            if user.avatar
            else None
        )
        response_data = {
            "email": user.email,
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_subscribed": user.is_subscribed,
            "avatar": avatar_url,
        }
        return Response(response_data, status=status.HTTP_200_OK)

    @action(["post"], detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(
            serializer.validated_data['current_password']
        ):
            return Response(
                {"current_password": ["Неверный текущий пароль."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()

    @action(["put", "delete"], detail=False, url_path='me/avatar')
    def avatar(self, request, *args, **kwargs):
        user = request.user
        if request.method == "PUT":
            avatar_data = request.data.get("avatar")
            if not avatar_data:
                return Response(
                    {"avatar": ["Обязательное поле."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                format, imgstr = avatar_data.split(';base64,')
                ext = format.split('/')[-1]
                decoded_file = base64.b64decode(imgstr)
                img_type = imghdr.what(None, decoded_file)
                if img_type != ext:
                    ext = img_type or ext
                file_name = f'{uuid.uuid4()}.{ext}'
                user.avatar.save(
                    file_name, ContentFile(decoded_file), save=True
                )
                avatar_url = (
                    request.build_absolute_uri(user.avatar.url)
                    if user.avatar
                    else None
                )
                return Response(
                    {
                        "avatar": avatar_url,
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response(
                    {"error": f"Ошибка при обработке изображения: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif request.method == "DELETE":
            if user.avatar.name:
                user.avatar.delete(save=True)
            return Response(
                status=status.HTTP_204_NO_CONTENT,
            )

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

    @action(
        detail=True,
        methods=['post', 'delete'],
    )
    def subscribe(self, request, id=None):
        try:
            user = request.user
            author = get_object_or_404(User, pk=id)

            if request.method == 'POST':
                if user == author:
                    return Response(
                        {'errors': 'Нельзя подписаться на самого себя'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if Follow.objects.filter(user=user, following=author).exists():
                    return Response(
                        {'errors': 'Вы уже подписаны на этого пользователя'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                Follow.objects.create(user=user, following=author)
                recipes_limit = request.query_params.get('recipes_limit')
                serializer = SubscriptionSerializer(
                    author,
                    context={
                        'request': request,
                        'recipes_limit': recipes_limit,
                    },
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

            if request.method == 'DELETE':
                follow = Follow.objects.filter(
                    user=user, following=author
                ).first()
                if not follow:
                    return Response(
                        {'errors': 'Вы не подписаны на этого пользователя'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response(
                {"detail": "Страница не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )


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

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related(
        'tags', 'ingredients', 'author'
    )
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise NotFound(detail="Страница не найдена.")

    @action(detail=True, methods=['get'])
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        short_link, created = ShortLink.objects.get_or_create(recipe=recipe)
        full_short_link = request.build_absolute_uri(
            f'/s/{short_link.short_url}/'
        )
        return Response(
            {'short-link': full_short_link}, status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            return self._add_to_favorite(user, recipe)
        elif request.method == 'DELETE':
            return self._remove_from_favorite(user, recipe)

    def _add_to_favorite(self, user, recipe):
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        Favorite.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe, context={'request': self.request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_favorite(self, user, recipe):
        favorite = Favorite.objects.filter(user=user, recipe=recipe).first()
        if not favorite:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
            user = request.user

            if request.method == 'POST':
                if ShoppingList.objects.filter(
                    user=user, recipe=recipe
                ).exists():
                    return Response(
                        {'errors': 'Рецепт уже в списке покупок'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                ShoppingList.objects.create(user=user, recipe=recipe)
                serializer = RecipeShortSerializer(
                    recipe, context={'request': request}
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

            elif request.method == 'DELETE':
                shopping_item = ShoppingList.objects.filter(
                    user=user, recipe=recipe
                ).first()

                if not shopping_item:
                    return Response(
                        {'errors': 'Рецепта нет в списке покупок'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                shopping_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

        except Http404:
            return Response(
                {"detail": "Страница не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

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

        lines = []
        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']
            lines.append(f"{name} ({unit}) — {amount:g}")

        content = "\n".join(lines)
        response = HttpResponse(
            content, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="shopping_list_{request.user.username}.txt"'
        )
        return response
