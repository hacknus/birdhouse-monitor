# birdhouse/asgi.py
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# Import the camera routing file
from camera.routing import websocket_urlpatterns  # Absolute import from the camera app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'birdhouse.settings')

# Routing setup for ASGI
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # HTTP requests handled by Django's default ASGI application
    "websocket": AuthMiddlewareStack(  # WebSocket connection setup
        URLRouter(
            websocket_urlpatterns  # WebSocket routing
        )
    ),
})