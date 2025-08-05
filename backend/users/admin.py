from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import UserProfile

class UserProfileAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('is_subscribed', 'avatar')}),
    )
    search_fields = ('email', 'username')

admin.site.register(UserProfile, UserProfileAdmin)
