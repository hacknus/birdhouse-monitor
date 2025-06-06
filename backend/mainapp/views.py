import json
import time
import datetime
import random

import cv2
import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse, HttpResponseNotFound
from django.shortcuts import render
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse

from .encoding import decode_email
from .models import SensorData, WeatherData
import csv
from django.shortcuts import render, redirect
from django.contrib import messages
import numpy as np
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

import mainapp.sensor_acquisition
import mainapp.weather_api
from .camera import camera_stream, turn_ir_on, turn_ir_off, get_ir_led_state


@csrf_exempt
def save_subscription(request):
    """ Save the push subscription """
    if request.method == "POST":
        data = json.loads(request.body)
        request.user.webpush_info = data
        request.user.save()
        return JsonResponse({"message": "Subscription saved successfully!"}, status=201)
    return JsonResponse({"error": "Invalid request"}, status=400)


def img_generator():
    while True:
        jpeg = camera_stream.get_jpeg()
        if jpeg is not None:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n\r\n"
            )
        else:
            time.sleep(0.1)

def video_feed(request):
    response = StreamingHttpResponse(
        img_generator(), content_type="multipart/x-mixed-replace;boundary=frame"
    )
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


def index(request):
    return render(request, "index.html")


def vogelguru(request):
    return render(request, "vogel_guru.html")


def save_image(request):
    if request.method == "POST":
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(settings.MEDIA_ROOT, "gallery", f"{timestamp}.jpg")

        frame = camera_stream.get_frame()

        cv2.imwrite(image_path, frame)

        return JsonResponse({"message": "Image saved! (this ma take a couple of seconds)",
                             "image_url": f"/media/gallery/{timestamp}.jpg"})

    return JsonResponse({"error": "Invalid request"}, status=400)


def gallery(request):
    # Get list of image files, ensuring they are sorted by filename (timestamp order)
    images = sorted(
        [f for f in os.listdir(os.path.join(settings.MEDIA_ROOT, "gallery")) if f.endswith((".jpg", ".png", ".jpeg"))],
        reverse=True  # Sort in descending order (newest first)
    )

    # Convert filenames to URLs
    image_urls = [os.path.join(settings.MEDIA_URL, "gallery", img) for img in images]
    images = []

    for image_url in image_urls:  # Replace with your actual image fetching logic
        filename = image_url.split("/")[-1].replace(".jpg", "")  # Extract filename
        dt = datetime.datetime.strptime(filename, "%Y%m%d_%H%M%S")  # Convert to datetime object
        formatted_datetime = dt.strftime("%Y-%m-%d %H:%M:%S")  # Format for display
        images.append({"url": image_url, "timestamp": formatted_datetime})

    return render(request, "gallery.html", {"images": images})


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


def get_ir_state(request):
    # You can access the IR state from wherever it's stored (e.g., in a variable, database, or hardware device)
    # For now, let's assume it’s stored in a variable or a simple flag.
    ir_led_state = "on" if get_ir_led_state() else "off"  # Replace 'ir_led_on' with the actual method/variable to fetch state.
    return JsonResponse({'state': ir_led_state})


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
            'number_of_visitors': entry.number_of_visitors,
            'timestamp': entry.timestamp.isoformat(),
        }
        for entry in data
    ]

    return JsonResponse(response_data, safe=False)


def get_guru_data(request):
    now = timezone.now()
    time_window = now - timedelta(hours=1)

    # Fetch sensor data based on the period
    data = SensorData.objects.filter(timestamp__gte=time_window).order_by('timestamp')
    local_temperature = data.latest("timestamp").temperature

    try:
        data = WeatherData.objects.filter(timestamp__gte=time_window).order_by('timestamp')
        bern_temperature = data.latest("timestamp").temperature
        # Prepare the data for the response
    except WeatherData.DoesNotExist:
        bern_temperature = local_temperature

    # load JSON data
    with open("mainapp/phrases.json", "r") as file:
        data = json.load(file)
        phrase = ""
        for key in data.keys():
            start, end = map(int, key.split(".."))  # Extract range bounds
            if start <= float(local_temperature) <= end:  # Check if value falls in the range
                phrase = random.choice(data[key])  # Pick a random element from the list
                break

    response_data = [
        {
            'temperatureValue': local_temperature,
            'temperatureBern': bern_temperature,
            'phrase': phrase,
        }
    ]
    print(response_data)

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
        email_list = read_email_list()

        # Check if the email is valid
        if email and email not in email_list:
            email_list.append(email)
            write_email_list(email_list)

            # Success message
            messages.success(request, f"Email {email} has been added to the newsletter list.")
        else:
            # Error message if email is empty or already exists
            messages.error(request, f"Invalid email or email already in the list: {email}")

        return redirect('newsletter')

def unsubscribe_email(request, email):
    """Handle the email unsubscription request."""
    email_list = read_email_list()
    email = decode_email(email)
    if email in email_list:
        email_list.remove(email)
        write_email_list(email_list)
        messages.success(request, f"{email} has been unsubscribed successfully.")
    else:
        messages.error(request, f"{email} was not found in the subscriber list.")

    return render(request, 'unsubscribe.html', {'email': email})


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
