import json
import time
import datetime
from random import random

import cv2
import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render

from picamera2 import Picamera2

from .models import SensorData
import mainapp.sensor_acquisition

# init camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (800, 600)}))
picam2.start()


def img_generator():
    while True:
        frame = picam2.capture_array()
        frame = frame[:, :, :-1]
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        # compression
        ret, jpeg = cv2.imencode(".jpg", frame)

        yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n\r\n"
        )


def video_feed(request):
    return StreamingHttpResponse(
        img_generator(), content_type="multipart/x-mixed-replace;boundary=frame"
    )


def index(request):
    return render(request, "index.html")


def save_image(request):
    if request.method == "POST":
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(settings.MEDIA_ROOT, "gallery", f"{timestamp}.jpg")

        frame = picam2.capture_array()
        frame = frame[:, :, :-1]
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        cv2.imwrite(image_path, frame)

        return JsonResponse({"message": "Image saved!", "image_url": f"/media/gallery/{timestamp}.jpg"})

    return JsonResponse({"error": "Invalid request"}, status=400)


def gallery(request):
    image_dir = os.path.join(settings.MEDIA_URL, "gallery/")

    try:
        image_files = os.listdir(os.path.join(settings.MEDIA_ROOT, "gallery"))
    except FileNotFoundError:
        image_files = []  # If the folder doesn't exist, return an empty list

    images = [{"url": f"{image_dir}{image}"} for image in image_files]

    return render(request, "gallery.html", {"images": images})


# Function to toggle the IR LED
def trigger_ir_led(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            action = data.get('action')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid request format.'}, status=400)

        import RPi.GPIO as GPIO
        # Toggle IR LED (ON or OFF)

        # Setup GPIO mode
        GPIO.setmode(GPIO.BCM)

        # Set the GPIO pin that controls the IR LED
        IR_LED_PIN = 17  # Change this pin number to match your setup
        GPIO.setup(IR_LED_PIN, GPIO.OUT)

        if action == 'on':
            GPIO.output(IR_LED_PIN, GPIO.HIGH)  # Turn the IR LED on
            return JsonResponse({'success': True, 'message': 'IR LED is ON.'})
        elif action == 'off':
            GPIO.output(IR_LED_PIN, GPIO.LOW)  # Turn the IR LED off
            return JsonResponse({'success': True, 'message': 'IR LED is OFF.'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action.'}, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)


def get_sensor_data(request):
    # Get the latest sensor data
    latest_data = SensorData.objects.last()

    if latest_data:
        data = {
            'temperature': latest_data.temperature,
            'humidity': latest_data.humidity,
            'motion_triggered': latest_data.motion_triggered,
            'timestamp': latest_data.timestamp.isoformat()  # Send timestamp in a JSON-compatible format
        }
    else:
        data = {
            'temperature': None,
            'humidity': None,
            'motion_triggered': None,
            'timestamp': None
        }

    return JsonResponse(data)