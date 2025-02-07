from django.contrib import admin
from django.urls import path, include
from .views import home  # Import the new homepage view

urlpatterns = [
    path("", home, name="home"),  # Set the home page
    path("admin/", admin.site.urls),
    path("camera/", include("camera.urls")),
    path("sensors/", include("sensors.urls")),  # Ensure you have a `sensors` app
    path("motion/", include("motion.urls")),  # Ensure you have a `motion` app
]
