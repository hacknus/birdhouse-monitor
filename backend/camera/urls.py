from django.urls import path
from . import views, consumers

app_name = 'camera'  # Add this line to define the app's namespace

urlpatterns = [
    path('', views.camera_home, name='camera_home'),
]

websocket_urlpatterns = [
    path('ws/camera/', consumers.CameraConsumer.as_asgi()),  # WebSocket for camera stream
]