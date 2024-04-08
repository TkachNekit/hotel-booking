from django.urls import include, path, re_path
from rest_framework import routers

from api.views import BookingModelViewSet, RoomModelViewSet

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'rooms', RoomModelViewSet)
router.register(r'bookings', BookingModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]
