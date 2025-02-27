# camera/routing.py
from django.urls import path
from .consumers import CameraConsumer

websocket_urlpatterns = [
    path('ws/camera/', CameraConsumer.as_asgi()),  # Make sure this URL matches the one in your frontend JavaScript
]