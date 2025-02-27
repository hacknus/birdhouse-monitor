import os
import platform
import time

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render


def home(request):
    return HttpResponse(
        "<h1>Welcome to the Birdhouse Monitor!</h1><p>Go to <a href='/camera/'>/camera/</a> to view the camera.</p>")


# Detect if running on Raspberry Pi
IS_RPI = os.environ.get('DOCKER_ENV', 'false') == 'true' or platform.system() == "Linux"

if IS_RPI:
    from picamera2 import Picamera2

    camera = Picamera2()
    camera.preview_configuration.size = (800, 600)
    camera.preview_configuration.format = "YUV420"
    camera.still_configuration.size = (1600, 1200)
    camera.still_configuration.enable_raw()
    camera.still_configuration.raw.size = camera.sensor_resolution


# Start the camera stream (assuming MJPEG or similar for live streaming)
def start_stream(request):
    # Ensure you have a live video stream
    camera.start("preview", show_preview=False)
    return JsonResponse({"status": "streaming started"})


# Capture image endpoint
def capture_image(request):
    # Define the filename and capture the image
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"media/{timestamp}.jpg"
    camera.capture(filename)

    # Return the captured image URL
    image_url = settings.MEDIA_URL + filename
    return JsonResponse({"image": image_url})


# View for gallery (display images from media folder)
def gallery(request):
    image_files = [f for f in os.listdir(settings.MEDIA_ROOT) if f.endswith('.jpg')]
    image_urls = [settings.MEDIA_URL + f for f in image_files]
    return JsonResponse({"images": image_urls})
