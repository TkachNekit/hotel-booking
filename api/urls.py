from django.urls import path

from api.views import RoomListAPIView

app_name = 'api'
urlpatterns = [
    path('room-list/', RoomListAPIView.as_view(), name='room_list'),    # GET .../api/room-list/
]
