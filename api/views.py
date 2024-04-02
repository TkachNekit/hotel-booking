from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet

from rooms.models import Room
from rooms.serializers import RoomSerializer


class RoomModelViewSet(ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
