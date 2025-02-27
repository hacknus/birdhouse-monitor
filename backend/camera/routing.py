# camera/routing.py
from django.urls import path
from .consumers import CameraConsumer

websocket_urlpatterns = [
    path('ws/camera/', CameraConsumer.as_asgi()),  # WebSocket for camera stream
]