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
import csv
from django.shortcuts import render, redirect
from django.contrib import messages
from picamera2 import Picamera2

from .models import SensorData
import mainapp.sensor_acquisition
import mainapp.interrupt

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
    # Get the period from the query parameters (default to '24h' if not provided)
    period = request.GET.get('period', '24h')
    now = timezone.now()

    # Calculate the time window based on the selected period
    if period == '24h':
        time_window = now - timedelta(hours=24)
    elif period == '7d':
        time_window = now - timedelta(days=7)
    elif period == '1m':
        time_window = now - timedelta(weeks=4)  # Approx 1 month
    elif period == '3m':
        time_window = now - timedelta(weeks=12)  # Approx 3 months
    elif period == 'all':
        time_window = None  # No time limit, fetch all data
    else:
        time_window = now - timedelta(hours=24)  # Default to '24h' if period is invalid

    # Fetch sensor data based on the period
    if time_window:
        data = SensorData.objects.filter(timestamp__gte=time_window).order_by('timestamp')
    else:
        data = SensorData.objects.all().order_by('timestamp')

    # Prepare the data for the response
    response_data = [
        {
            'temperature': entry.temperature,
            'humidity': entry.humidity,
            'motion_triggered': entry.motion_triggered,
            'timestamp': entry.timestamp.isoformat(),
        }
        for entry in data
    ]

    return JsonResponse(response_data, safe=False)


# Path to the CSV file where emails are stored
CSV_FILE_PATH = 'newsletter_subscribers.csv'


# Read the current list of emails from the CSV file
def read_email_list():
    try:
        with open(CSV_FILE_PATH, mode='r') as file:
            reader = csv.reader(file)
            return [row[0] for row in reader]
    except FileNotFoundError:
        return []


# Write the email list back to the CSV file
def write_email_list(email_list):
    with open(CSV_FILE_PATH, mode='w') as file:
        writer = csv.writer(file)
        for email in email_list:
            writer.writerow([email])


# View for the newsletter page
def newsletter(request):
    # Get the current email list to display it on the page
    email_list = read_email_list()
    return render(request, 'newsletter.html', {'email_list': email_list})


# Add an email to the list
def add_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # Check if the email is valid
        if email and email not in read_email_list():
            email_list = read_email_list()
            email_list.append(email)
            write_email_list(email_list)

            # Success message
            messages.success(request, f"Email {email} has been added to the newsletter list.")
        else:
            # Error message if email is empty or already exists
            messages.error(request, f"Invalid email or email already in the list: {email}")

        return redirect('newsletter')


# Remove an email from the list
def remove_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        email_list = read_email_list()
        if email in email_list:
            email_list.remove(email)
            write_email_list(email_list)

            # Success message
            messages.success(request, f"Email {email} has been removed from the newsletter list.")
        else:
            # Error message if email is not found
            messages.error(request, f"Email {email} is not in the list.")

        return redirect('newsletter')
