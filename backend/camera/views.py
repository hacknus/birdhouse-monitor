import io
import os
import platform
import time
from threading import Condition, Thread

from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render

from datetime import datetime

# Detect if running on Raspberry Pi
IS_RPI = os.environ.get('DOCKER_ENV', 'false') == 'true' or platform.system() == "Linux"

if IS_RPI:
    from picamera2 import Picamera2
    from picamera2.encoders import JpegEncoder
    from picamera2.outputs import FileOutput

    camera = Picamera2()

    camera.preview_configuration.size = (800, 600)
    camera.preview_configuration.format = "YUV420"
    camera.still_configuration.size = (1600, 1200)
    camera.still_configuration.enable_raw()
    camera.still_configuration.raw.size = camera.sensor_resolution
    camera.configure(camera.create_video_configuration(main={"size": (640, 480)}))

else:
    camera = None  # Mock camera


# The StreamingOutput class handles the video stream
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


# Global variable to hold the output object for the stream
output = StreamingOutput()
clients = []  # To keep track of connected clients
streaming_thread = None


def camera_home(request):
    # Gallery images
    image_dir = os.path.join(settings.MEDIA_ROOT, 'captured_images')
    gallery_images = []
    if os.path.exists(image_dir):
        gallery_images = [f'captured_images/{f}' for f in os.listdir(image_dir) if f.endswith('.jpg')]

    return render(request, 'camera/index.html', {'gallery_images': gallery_images})


def start_stream():
    """Start the camera stream in a background thread if it's not already started."""
    global streaming_thread

    if streaming_thread is None:
        def camera_stream():
            """Run the camera capture in a separate thread to keep the stream active."""
            camera.stop_recording()
            camera.configure(camera.create_video_configuration(main={"size": (640, 480)}))
            camera.start_recording(JpegEncoder(), FileOutput(output))

        # Start the camera streaming thread
        streaming_thread = Thread(target=camera_stream)
        streaming_thread.daemon = True  # Daemon thread will exit when the main program exits
        streaming_thread.start()


def stop_stream():
    """Stop the camera stream."""
    global streaming_thread

    if streaming_thread is not None:
        camera.stop_recording()
        streaming_thread = None
        print("Camera stream stopped.")


def stream_mjpg(request):
    """Handle the MJPEG stream."""
    start_stream()  # Ensure the camera starts if it's the first client

    def gen():
        """Generator function to send the MJPEG frames to the client."""
        while True:
            with output.condition:
                output.condition.wait()  # Wait for the next frame
                frame = output.frame
            # Yield the frame in MJPEG format with necessary headers
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            time.sleep(0.1)  # Add a small delay to avoid excessive CPU usage

    # Add the client to the list of connected clients
    clients.append(request)

    # Return the streaming HTTP response
    response = StreamingHttpResponse(gen(), content_type='multipart/x-mixed-replace; boundary=frame')

    # Clean up when the client disconnects
    def on_disconnect():
        # Remove the client from the list when they disconnect
        clients.remove(request)
        if len(clients) == 0:
            stop_stream()

    request._close = on_disconnect
    return response


def stop_camera(request):
    """Stop the camera stream."""
    stop_stream()
    return JsonResponse({"status": "Camera stopped."})
