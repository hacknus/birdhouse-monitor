from django.urls import path
from . import views

urlpatterns = [
    path('', views.camera_home, name='camera_home'),
    path('camera/start_stream/', views.start_stream, name='start_stream'),
    path('camera/stream.mjpg', views.stream_mjpg, name='stream_mjpg'),
    path('camera/stop/', views.stop_camera, name='stop_camera'),
]