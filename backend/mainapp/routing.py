from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Define the WebSocket route to handle the video feed
    re_path(r'ws/video_feed/$', consumers.VideoStreamConsumer.as_asgi()),
]