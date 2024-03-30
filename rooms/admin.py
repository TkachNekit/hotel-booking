from django.contrib import admin
from rooms.models import RoomType, Room
from users.models import User, TelegramAuthorization

admin.site.register(Room)
admin.site.register(RoomType)
admin.site.register(User)
admin.site.register(TelegramAuthorization)
