# birdhouse/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from camera.routing import websocket_urlpatterns  # Import the WebSocket routing from camera app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'birdhouse.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  # This ensures that WebSocket traffic is routed to the CameraConsumer
        )
    ),
})