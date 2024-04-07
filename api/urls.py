from django.urls import include, path
from rest_framework import routers

from api.views import BookingModelViewSet, RoomModelViewSet

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'rooms', RoomModelViewSet)
router.register(r'bookings', BookingModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
