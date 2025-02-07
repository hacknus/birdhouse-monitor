from django.urls import path
from .views import camera_home, capture_image, toggle_ir

urlpatterns = [
    path("", camera_home, name="camera_home"),  # <-- Add this line
    path("capture/", capture_image, name="capture_image"),
    path("toggle_ir/", toggle_ir, name="toggle_ir"),
]