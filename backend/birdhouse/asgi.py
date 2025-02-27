# backend/birdhouse/asgi.py
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# Import websocket URL routing from camera app using absolute import
from camera.routing import websocket_urlpatterns  # Absolute import for camera

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'birdhouse.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Handle HTTP requests
    "websocket": AuthMiddlewareStack(  # Handle WebSocket connections
        URLRouter(
            websocket_urlpatterns  # Include WebSocket URLs from camera app
        )
    ),
})