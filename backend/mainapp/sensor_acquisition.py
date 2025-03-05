import csv
import datetime
import os
import threading

from django.conf import settings
from gpiozero import MotionSensor

import time
import board
import adafruit_sht4x

# replace this with custom email-interface
from unibe_mail import Reporter
import cv2

# Import your Django model
from .models import SensorData
from .camera import picam2, turn_ir_on, turn_ir_off, get_ir_led_state

# I2C sensor setup
i2c = board.I2C()
sensor = adafruit_sht4x.SHT4x(i2c)

# GPIO Motion Sensor Setup
MOTION_PIN = 4
pir = MotionSensor(MOTION_PIN, threshold=0.8, queue_len=10)

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


# Track last image save time and last email sent time
last_image_time = 0
last_email_time = 0
ignore_motion_until = 0  # Timestamp until which motion detection is ignored


def ignore_motion_for(seconds):
    """Temporarily disable motion detection for a given number of seconds."""
    global ignore_motion_until
    ignore_motion_until = time.time() + seconds


def motion_detected_callback():
    global last_image_time, last_email_time, ignore_motion_until

    current_time = time.time()

    # Check if motion detection should be ignored
    if current_time < ignore_motion_until or get_ir_led_state():
        print("Motion detection ignored.")
        return

    temperature, humidity = read_temperature_humidity()
    store_sensor_data(temperature, humidity, motion_triggered=True)

    # Save an image only if at least an hour has passed
    if current_time - last_image_time >= 3600:
        # todo: only do this if the light is not on
        turn_ir_on()
        time.sleep(3)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(settings.MEDIA_ROOT, "gallery", f"{timestamp}.jpg")

        frame = picam2.capture_array()
        frame = frame[:, :, :-1]
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        cv2.imwrite(image_path, frame)
        last_image_time = current_time

        turn_ir_off()

    # Send an email only if at least a day has passed
    if current_time - last_email_time >= 86400:
        try:
            csv_file = 'newsletter_subscribers.csv'
            with open(csv_file, mode='r') as file:
                reader = csv.reader(file)
                subscribers = list(reader)
                for subscriber in subscribers:
                    Voegeli.send_mail(
                        f"Hoi Du!\nI'm moving into the birdhouse!\nCheck me out at http://cgnum.space.unibe.ch/voegeli\nBest Regards, Your Vögeli",
                        subject="Vögeli Motion Alert",
                        recipients=subscriber[0]
                    )
            last_email_time = current_time
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
