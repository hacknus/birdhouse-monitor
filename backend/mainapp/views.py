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

from .models import SensorData
import mainapp.sensor_acquisition
from .camera import picam2, turn_ir_on, turn_ir_off


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

    # Get list of image files, ensuring they are sorted by filename (timestamp order)
    images = sorted(
        [f for f in os.listdir(os.path.join(settings.MEDIA_ROOT, "gallery")) if f.endswith((".jpg", ".png", ".jpeg"))],
        reverse=True  # Sort in descending order (newest first)
    )

    # Convert filenames to URLs
    image_urls = [os.path.join(settings.MEDIA_URL, "gallery", img) for img in images]

    return render(request, "gallery.html", {"images": image_urls})


# Function to toggle the IR LED
def trigger_ir_led(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            action = data.get('action')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid request format.'}, status=400)

        if action == 'on':
            turn_ir_on()
            return JsonResponse({'success': True, 'message': 'IR LED is ON.'})
        elif action == 'off':
            turn_ir_off()
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


def newsletter_view(request):
    # Path to the CSV file where emails are stored
    csv_file = 'newsletter_subscribers.csv'

    # Read the current subscribers from the CSV file
    subscribers = []
    try:
        with open(csv_file, mode='r') as file:
            reader = csv.reader(file)
            subscribers = list(reader)
    except FileNotFoundError:
        pass  # File does not exist yet, no subscribers

    # Pass the number of subscribers to the template
    return render(request, 'newsletter.html', {
        'subscriber_count': len(subscribers),
    })


def making_of_view(request):
    return render(request, 'making_of.html')
