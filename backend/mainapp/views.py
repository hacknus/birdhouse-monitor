import json
import time
import datetime
from random import random

import cv2
import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from .models import SensorData

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
    # Get the 'period' query parameter (default to '24h' if not provided)
    period = request.GET.get('period', '24h')

    # Get the current time
    now = timezone.now()

    # Calculate the start time based on the period
    if period == '24h':
        start_time = now - timedelta(hours=24)
    elif period == '7d':
        start_time = now - timedelta(days=7)
    elif period == '1m':
        start_time = now - timedelta(weeks=4)  # Roughly one month
    elif period == '3m':
        start_time = now - timedelta(weeks=12)  # Roughly three months
    elif period == 'all':
        start_time = None  # No filtering by time
    else:
        start_time = now - timedelta(hours=24)  # Default to '24h' if invalid period

    # Filter the sensor data by the calculated start time
    if start_time:
        sensor_data = SensorData.objects.filter(timestamp__gte=start_time)
    else:
        sensor_data = SensorData.objects.all()

    # Prepare the data to send to the client (only send the necessary fields)
    data = []
    for entry in sensor_data:
        data.append({
            'temperature': entry.temperature,
            'humidity': entry.humidity,
            'motion_triggered': entry.motion_triggered,
            'timestamp': entry.timestamp.isoformat()  # Send timestamp in a JSON-compatible format
        })

    return JsonResponse(data, safe=False)