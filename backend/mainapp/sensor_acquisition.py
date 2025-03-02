import csv
import datetime
import os
import threading

from django.conf import settings
from django.http import HttpRequest, QueryDict
from gpiozero import MotionSensor

import time
import board
import adafruit_sht4x

# replace this with custom email-interface
from unibe_mail import Reporter
import cv2

# Import your Django model
from .models import SensorData
from .camera import picam2

# I2C sensor setup
i2c = board.I2C()
sensor = adafruit_sht4x.SHT4x(i2c)

# GPIO Motion Sensor Setup
MOTION_PIN = 4
pir = MotionSensor(MOTION_PIN)

# email callback

# replace this with custom email-interface
Voegeli = Reporter("Voegeli")


# Function to read temperature and humidity
def read_temperature_humidity():
    temperature = round(sensor.temperature, 2)
    humidity = round(sensor.relative_humidity, 2)
    return temperature, humidity


# Function to store sensor data in the database
def store_sensor_data(temperature, humidity, motion_triggered):
    SensorData.objects.create(
        temperature=temperature,
        humidity=humidity,
        motion_triggered=motion_triggered
    )


# Motion detection callback (interrupt-based)
def motion_detected_callback():
    temperature, humidity = read_temperature_humidity()
    store_sensor_data(temperature, humidity, motion_triggered=True)

    csv_file = 'newsletter_subscribers.csv'

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = os.path.join(settings.MEDIA_ROOT, "gallery", f"{timestamp}.jpg")

    frame = picam2.capture_array()
    frame = frame[:, :, :-1]
    frame = cv2.rotate(frame, cv2.ROTATE_180)

    cv2.imwrite(image_path, frame)
    # Read the current subscribers from the CSV file and send emails
    try:
        with open(csv_file, mode='r') as file:
            reader = csv.reader(file)
            subscribers = list(reader)
            for subscriber in subscribers:
                Voegeli.send_mail(
                    f"Hoi Du!\nI'm moving into the birdhouse!\nCheck me out at http://cgnum.space.ch/voegeli or at http://130.92.145.222\nBest Regards, Your Vögeli",
                    subject="Vögeli Motion Alert",
                    recipients=subscriber[0])
    except FileNotFoundError:
        pass  # File does not exist yet, no subscribers

    print("Motion detected! Data stored.")


time.sleep(1)  # Wait for hardware to settle


# Background thread for temperature/humidity logging (runs every 60s)
def periodic_data_logger():
    # Register interrupt for motion detection (FALLING or RISING can be used)
    pir.when_motion = motion_detected_callback
    while True:
        temperature, humidity = read_temperature_humidity()
        store_sensor_data(temperature, humidity, motion_triggered=False)
        time.sleep(60)


# Start background thread
data_thread = threading.Thread(target=periodic_data_logger, daemon=True)
data_thread.start()
