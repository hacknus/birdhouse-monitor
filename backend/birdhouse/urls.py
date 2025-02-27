# birdhouse/urls.py
from django.urls import path, include

urlpatterns = [
    path('camera/', include('camera.urls', namespace='camera')),  # For HTTP
]