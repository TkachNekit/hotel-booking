from rest_framework.generics import ListAPIView

from rooms.models import Room
from rooms.serializers import RoomSerializer


class RoomListAPIView(ListAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
