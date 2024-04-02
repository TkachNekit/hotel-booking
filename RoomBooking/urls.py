from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    path('api-token-auth/', obtain_auth_token),

]
