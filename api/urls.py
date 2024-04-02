from django.urls import include, path
from rest_framework import routers

from api.views import RoomModelViewSet

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'rooms', RoomModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
