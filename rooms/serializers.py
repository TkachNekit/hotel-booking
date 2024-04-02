from rest_framework import serializers

from rooms.models import Room, RoomType


class RoomSerializer(serializers.ModelSerializer):
    type = serializers.SlugRelatedField(slug_field='name', queryset=RoomType.objects.all())

    class Meta:
        model = Room
        fields = ('id', 'number', 'type', 'current_price', 'capacity', 'description')
