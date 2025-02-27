# camera/urls.py
from django.urls import path
from . import views

app_name = 'camera'  # This sets the namespace for this app's URLs

urlpatterns = [
    path('', views.camera_home, name='camera_home'),  # Home page for camera
    # path('gallery/', views.get_gallery, name='gallery'),  # Gallery page
    # path('stream/', views.stream_mjpg, name='stream'),  # MJPEG stream endpoint
    # path('capture/', views.capture_image, name='capture'),  # Capture image endpoint
]