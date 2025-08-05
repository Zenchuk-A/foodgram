import base64

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.exceptions import NotAuthenticated
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.contrib.auth.validators import UnicodeUsernameValidator

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Follow,
    Favorite,
    ShoppingList,
    IngredientRecipe,
    RECIPE_NAME_MAX_LENGTH,
)
from users.models import UserProfile, USERNAME_MAX_LENGTH
from users.validators import forbidden_names_validator


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserProfileSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    first_name = serializers.CharField(
        required=True, max_length=USERNAME_MAX_LENGTH
    )
    last_name = serializers.CharField(
        required=True, max_length=USERNAME_MAX_LENGTH
    )
    email = serializers.EmailField(required=True)
    username = serializers.CharField(
        required=True,
        max_length=USERNAME_MAX_LENGTH,
        validators=[UnicodeUsernameValidator(), forbidden_names_validator],
    )

    password = serializers.CharField(write_only=True, required=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
            'avatar',
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = UserProfile(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def get_image_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        else:
            return None

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return user.follower.filter(following=obj).exists()

    def validate_email(self, value):
        if UserProfile.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.'
            )
        else:
            return value

    def validate_username(self, value):
        if UserProfile.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким именем уже существует.'
            )
        else:
            return value


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def to_internal_value(self, data):
        return {'ingredient': data['id'], 'amount': data['amount']}


class RecipeSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
    )
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='recipe_ingredients',
        required=True,
    )
    name = serializers.CharField(
        required=True, max_length=RECIPE_NAME_MAX_LENGTH
    )
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(required=True, min_value=1)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = (
            'id',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def validate(self, data):
        request = self.context.get('request')
        if request and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            if not request.user.is_authenticated:
                raise NotAuthenticated("Учетные данные не были предоставлены.")

        required_fields = [
            'name',
            'text',
            'cooking_time',
            'tags',
            'recipe_ingredients',
        ]
        errors = {}

        for field in required_fields:
            if field not in data:
                display_field = (
                    'ingredients' if field == 'recipe_ingredients' else field
                )
                errors[display_field] = 'Это поле обязательно.'

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True
        ).data

        return representation

    def get_ingredients(self, obj):
        ingredients = IngredientRecipe.objects.filter(recipe=obj)
        return IngredientRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingList.objects.filter(user=user, recipe=obj).exists()

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )
        ingredient_ids = [item['ingredient'] for item in value]
        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.'
            )

        existing_ids = set(
            Ingredient.objects.filter(id__in=ingredient_ids).values_list(
                'id', flat=True
            )
        )

        missing_ids = set(ingredient_ids) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                {
                    'ingredients': f'Ингредиенты с id {missing_ids} '
                    'не существуют.'
                }
            )

        errors = []
        for i, item in enumerate(value):
            item_errors = {}
            if float(item['amount']) <= 0:
                item_errors['amount'] = [
                    'Убедитесь, что это значение больше либо равно 1.'
                ]

            if item_errors:
                errors.append(item_errors)
            else:
                errors.append({})

        if any(errors):
            raise serializers.ValidationError(errors)

        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Добавьте хотя бы один тег.')
        tag_ids = [tag.id for tag in value]
        if len(set(tag_ids)) != len(tag_ids):
            raise serializers.ValidationError(
                {'tags': 'Теги должны быть уникальными.'},
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            self._create_ingredients(instance, ingredients)

        return instance

    def _create_ingredients(self, recipe, ingredients):
        objs = []
        for item in ingredients:
            ingredient = Ingredient.objects.get(id=item['ingredient'])
            amount = item['amount']
            objs.append(
                IngredientRecipe(
                    recipe=recipe, ingredient=ingredient, amount=amount
                )
            )
        IngredientRecipe.objects.bulk_create(objs)


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    following = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all()
    )
    user = serializers.SlugRelatedField(
        slug_field='username',
        default=serializers.CurrentUserDefault(),
        read_only=True,
    )

    class Meta:
        fields = ('user', 'following')
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(), fields=('user', 'following')
            )
        ]

    def validate_following(self, value):
        user = self.context['request'].user
        if user == value:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя."
            )

        return value


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(user=request.user, following=obj).exists()

    def get_recipes(self, obj):
        recipes_limit = self.context.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        serializer = RecipeShortSerializer(
            recipes,
            many=True,
            context={'request': self.context.get('request')},
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'recipe', 'user')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(), fields=('user', 'recipe')
            )
        ]


class ShoppingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = ('id', 'recipe', 'user')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(), fields=('user', 'recipe')
            )
        ]


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        user = self.context['request'].user
        validate_password(password=value, user=user)
        return value
