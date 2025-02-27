from django.contrib import admin
from django.urls import path, include
from .views import home  # Import the new homepage view
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
                  path("", home, name="home"),  # Set the home page
                  path("admin/", admin.site.urls),
                  path("camera/", include("camera.urls")),
                  path('camera/start_stream/', views.start_stream, name='start_stream'),
                  path('camera/capture/', views.capture_image, name='capture_image'),
                  path('camera/gallery/', views.gallery, name='gallery'),
                  path("sensors/", include("sensors.urls")),  # Ensure you have a `sensors` app
                  path("motion/", include("motion.urls")),  # Ensure you have a `motion` app
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
