from django.contrib import admin
from users.models import User, TelegramAuthorization


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name')


@admin.register(TelegramAuthorization)
class TelegramAuthorizationAdmin(admin.ModelAdmin):
    list_display = ('user', 'telegram_id',)
    fields = ('user', 'telegram_id', 'authorization_date')
    readonly_fields = ('authorization_date',)
