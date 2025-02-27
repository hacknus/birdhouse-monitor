from django.urls import path
from .views import camera_home, capture_image, toggle_ir, start_stream, gallery

urlpatterns = [
    path("", camera_home, name="camera_home"),  # Home page for the camera (live-stream or controls)
    path("capture/", capture_image, name="capture_image"),  # Capture image
    path("toggle_ir/", toggle_ir, name="toggle_ir"),  # Toggle IR light
    path("live/", start_stream, name="live_stream"),  # Live stream view
    path("gallery/", gallery, name="gallery"),  # Gallery to view captured images
]