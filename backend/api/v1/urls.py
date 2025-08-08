from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, ProfileViewSet, RecipesViewSet,
                    TagViewSet)

router_v1 = DefaultRouter()
router_v1.register('users', ProfileViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('recipes', RecipesViewSet, basename='recipes')

urlpatterns = [
    path('', include(router_v1.urls)),
    path(
        'recipes/<int:pk>/get-link/',
        RecipesViewSet.as_view({'get': 'get_short_link'}),
        name='get-short-link',
    ),
    path('auth/', include('djoser.urls.authtoken')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
