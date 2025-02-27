# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from camera.consumers import CameraConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'birdhouse-monitor.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/camera/", CameraConsumer.as_asgi()),  # WebSocket URL
        ])
    ),
})