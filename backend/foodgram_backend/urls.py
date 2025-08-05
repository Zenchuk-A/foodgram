from django.contrib import admin
from django.urls import path, include, re_path

from api.v1.views import redirect_to_recipe

urlpatterns = [
    # path(
    #     's/<str:short_url>/',
    #     redirect_to_recipe,
    #     name='short-link-redirect',
    # ),
    re_path(
        r'^s/(?P<short_url>[^/]+)/?$',
        redirect_to_recipe,
        name='short-link-redirect',
    ),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
