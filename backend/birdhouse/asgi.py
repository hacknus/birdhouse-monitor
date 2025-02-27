import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from camera import routing  # Add this line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'birdhouse.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns  # Use the routing from the camera app
        )
    ),
})