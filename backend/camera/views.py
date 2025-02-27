# backend/camera/views.py

from django.http import StreamingHttpResponse
from livestream.stream import CameraStream

# Initialize the camera stream object
camera_stream = CameraStream()

def video_feed(request):
    """Django view to stream the video feed"""
    return StreamingHttpResponse(camera_stream.gen(), content_type='multipart/x-mixed-replace; boundary=frame')