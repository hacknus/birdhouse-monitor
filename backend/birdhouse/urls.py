# birdhouse/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('camera/', include('camera.urls')),  # Regular camera URLs (like capturing images)
]