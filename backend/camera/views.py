import io
import os
import platform
import time
from threading import Condition

from django.conf import settings
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import render

from datetime import datetime

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

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

def camera_home(request):
    # Gallery images
    image_dir = os.path.join(settings.MEDIA_ROOT, 'captured_images')
    gallery_images = []

    if os.path.exists(image_dir):
        gallery_images = [f'captured_images/{f}' for f in os.listdir(image_dir) if f.endswith('.jpg')]

    return render(request, 'camera/index.html', {'gallery_images': gallery_images})


def stream_mjpg(request):
    output = StreamingOutput()

    # Ensure the camera is stopped before reconfiguring it
    if camera.recording:
        camera.stop_recording()

    # Configure the camera for MJPEG streaming
    camera.configure(camera.create_video_configuration(main={"size": (640, 480)}))
    camera.start_recording(JpegEncoder(), FileOutput(output))

    # Create a response for MJPEG streaming
    response = HttpResponse(content_type="multipart/x-mixed-replace; boundary=FRAME")
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'

    try:
        while True:
            with output.condition:
                output.condition.wait()  # Wait for a new frame
                frame = output.frame  # Get the latest frame

            # Send the frame to the client as part of the MJPEG stream
            response.write(b'--FRAME\r\n')
            response.write(b'Content-Type: image/jpeg\r\n')
            response.write(f'Content-Length: {len(frame)}\r\n'.encode())
            response.write(b'\r\n')  # End of headers
            response.write(frame)
            response.write(b'\r\n')  # End of frame

    except Exception as e:
        camera.stop_recording()
        print(f"Error during streaming: {e}")
        return HttpResponse(status=500)

    # The response will continue to stream until the connection is closed
    return response

def stop_camera(request):
    camera.stop_recording()
    return HttpResponse("Camera stopped.")

def capture_image(request):
    """Capture image from camera (real on Pi, placeholder on macOS)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if IS_RPI:
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        image_path = os.path.join(settings.MEDIA_ROOT, filename)

        # Debugging
        print(f"Saving image to: {image_path}")

        # Ensure the camera is stopped before reconfiguring it
        if camera.recording:
            camera.stop_recording()

        camera.start("preview", show_preview=False)
        time.sleep(2)

        camera.switch_mode_and_capture_file("still", image_path)

        camera.stop()

    else:
        filename = "static/test_image.jpg"  # Placeholder image on macOS

    return JsonResponse({"image": f"{settings.MEDIA_URL}{filename}"})


def toggle_ir(request):
    """Toggle IR LED (real on Pi, mock on macOS)."""
    state = request.GET.get("state", "off")

    if IS_RPI:
        import RPi.GPIO as GPIO
        IR_PIN = 17
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(IR_PIN, GPIO.OUT)
        GPIO.output(IR_PIN, GPIO.HIGH if state == "on" else GPIO.LOW)

    return JsonResponse({"status": f"IR light {state}"})