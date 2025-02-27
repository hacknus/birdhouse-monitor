import os
import platform

from django.http import JsonResponse

# Detect if running on Raspberry Pi
IS_RPI = os.environ.get('DOCKER_ENV', 'false') == 'true' or platform.system() == "Linux"

if IS_RPI:
    from gpiozero import MotionSensor

    pir = MotionSensor(4)
else:
    pir = None  # Mock motion sensor

motion_detected = False  # Default state


def motion_status(request):
    """Get motion sensor status (real on Pi, mock on macOS)."""
    global motion_detected

    if IS_RPI:
        motion_detected = pir.motion_detected
    else:
        motion_detected = not motion_detected  # Toggle status for testing

    return JsonResponse({"motion": "active" if motion_detected else "inactive"})