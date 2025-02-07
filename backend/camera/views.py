import os
import platform
from django.http import JsonResponse
from django.shortcuts import render

from datetime import datetime

# Detect if running on Raspberry Pi
IS_RPI = platform.system() == "Linux" and os.path.exists("/sys/firmware/devicetree/base/model")

if IS_RPI:
    from picamera2 import Picamera2

    camera = Picamera2()
    camera.start()
else:
    camera = None  # Mock camera

def camera_home(request):
    return render(request, "camera/index.html")

def capture_image(request):
    """Capture image from camera (real on Pi, placeholder on macOS)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if IS_RPI:
        filename = f"media/{timestamp}.jpg"
        camera.capture_file(filename)
    else:
        filename = "static/test_image.jpg"  # Placeholder image on macOS

    return JsonResponse({"image": filename})


def toggle_ir(request):
    """Toggle IR LED (real on Pi, mock on macOS)."""
    state = request.GET.get("state", "off")

    if IS_RPI:
        import RPi.GPIO as GPIO
        IR_PIN = 17  # Change as needed
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(IR_PIN, GPIO.OUT)
        GPIO.output(IR_PIN, GPIO.HIGH if state == "on" else GPIO.LOW)

    return JsonResponse({"status": f"IR light {state}"})