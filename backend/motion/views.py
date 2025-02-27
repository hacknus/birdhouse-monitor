import os
import platform
import threading
import time

from django.http import JsonResponse

# Detect if running on Raspberry Pi
IS_RPI = os.environ.get('DOCKER_ENV', 'false') == 'true' or platform.system() == "Linux"

if IS_RPI:
    from gpiozero import MotionSensor

    pir = MotionSensor(4)
else:
    pir = None  # Mock motion sensor

motion_detected = False  # Default state


def update_motion_data():
    global motion_data
    while True:
        if IS_RPI:
            motion_detected = pir.motion_detected
        else:
            motion_detected = not motion_detected  # Toggle status for testing
        motion_data = motion_detected
        time.sleep(3)  # Update every 3 seconds


# Start the sensor data update in a separate thread
motion_thread = threading.Thread(target=update_motion_data)
motion_thread.daemon = True  # Daemon thread will automatically exit when the main program exits
motion_thread.start()


def motion_status(request):
    # Return the current sensor data as a JSON response
    return JsonResponse({"motion": "active" if motion_data else "inactive"})