from django.contrib import admin
from django.urls import path, include
from .views import home  # Import the new homepage view
from django.conf import settings
from django.conf.urls.static import static
from . import views, consumers

urlpatterns = [
                  path("", home, name="home"),  # Set the home page
                  path("admin/", admin.site.urls),
                  path('camera/', include('camera.urls', namespace='camera')),  # Add the namespace here
                  path("sensors/", include("sensors.urls")),  # Ensure you have a `sensors` app
                  path("motion/", include("motion.urls")),  # Ensure you have a `motion` app
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

websocket_urlpatterns = [
    path('ws/camera/',  include('camera.urls', namespace='camera')),  # WebSocket for camera stream
]