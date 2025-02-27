from django.urls import path
from .views import camera_home, capture_image, toggle_ir, start_stream, stream_mjpg, stop_camera

app_name = 'camera'  # Add this line to define the app's namespace

urlpatterns = [
    path("", camera_home, name="camera_home"),  # <-- Add this line
    path("capture/", capture_image, name="capture_image"),  # Capture image
    path("toggle_ir/", toggle_ir, name="toggle_ir"),  # Toggle IR light
    path('start_stream/', start_stream, name='start_stream'),
    path('stream.mjpg', stream_mjpg, name='stream_mjpg'),
    path('stop/', stop_camera, name='stop_camera'),  # Stop the camera
]
