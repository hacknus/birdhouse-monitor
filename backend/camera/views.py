import io
import os
import platform
import time

from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

from datetime import datetime

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

else:
    camera = None  # Mock camera


def camera_home(request):
    return render(request, "camera/index.html")


# Start the camera stream (assuming MJPEG or similar for live streaming)
def start_stream(request):
    # Ensure you have a live video stream
    camera.start("preview", show_preview=False)

    # Create an HTTP response for streaming MJPEG
    response = HttpResponse(content_type="multipart/x-mixed-replace; boundary=frame")

    try:
        while True:
            # Capture the image in memory without saving to disk
            img_byte_arr = io.BytesIO()

            # Capture the image and save it directly to the memory buffer in JPEG format
            camera.capture_array("raw").tofile(img_byte_arr)
            img_byte_arr.seek(0)

            # Write the boundary and image data to the response
            response.write(b'--frame\r\n')
            response.write(b'Content-Type: image/jpeg\r\n\r\n')
            response.write(img_byte_arr.read())
            response.write(b'\r\n')

            # Flush the response to send it to the client
            response.flush()

            # Add a small delay to prevent overloading the CPU
            time.sleep(0.1)

    except GeneratorExit:
        # Stop the camera if the client disconnects
        camera.stop()

    return response


def capture_image(request):
    """Capture image from camera (real on Pi, placeholder on macOS)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if IS_RPI:
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        image_path = os.path.join(settings.MEDIA_ROOT, filename)

        # Debugging
        print(f"Saving image to: {image_path}")

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


# Gallery view
def gallery(request):
    # List all files in the media directory (assumes images are stored here)
    image_dir = os.path.join(settings.MEDIA_ROOT, "camera")  # Or wherever the images are stored
    image_files = [f for f in os.listdir(image_dir) if f.endswith('.jpg')]
    image_urls = [os.path.join("media", f) for f in image_files]

    return render(request, "camera/gallery.html", {"images": image_urls})