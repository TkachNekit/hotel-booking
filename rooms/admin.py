from django.contrib import admin

from rooms.models import Room, RoomType


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'type', 'current_price')
    fields = ('id', 'number', 'type', 'current_price', 'capacity', 'description')
    readonly_fields = ('id',)


admin.site.register(RoomType)
