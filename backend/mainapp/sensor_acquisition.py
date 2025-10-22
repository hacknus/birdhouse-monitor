import csv
import datetime
import os
import sqlite3
import threading
from django.contrib.auth.models import User

from django.conf import settings
from django.db.utils import OperationalError
from gpiozero import MotionSensor

import time
import board
import adafruit_sht4x

# replace this with custom email-interface
from unibe_mail import Reporter
import cv2

from .encoding import encode_email
from .ignore_motion import are_we_still_blocked
# Import your Django model
from .models import SensorData
from .camera import camera_stream, turn_ir_on, turn_ir_off, get_ir_led_state
from .push_notifications import send_push_notification
from .middleware import get_active_visitors

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
    try:
        SensorData.objects.create(
            temperature=temperature,
            humidity=humidity,
            motion_triggered=motion_triggered,
            number_of_visitors=get_active_visitors(),
        )
    except (OperationalError, sqlite3.OperationalError):
        pass


# Track last image save time and last email sent time
last_image_time = 0


def motion_detected_callback():
    global last_image_time

    # Check if motion detection should be ignored
    if are_we_still_blocked():
        print("Motion detection temporarily ignored.")
        return
    if get_ir_led_state():
        print("Motion detection ignored because IR LED is on.")
        return

    current_time = time.time()
    temperature, humidity = read_temperature_humidity()
    store_sensor_data(temperature, humidity, motion_triggered=True)

    users = User.objects.all()
    for user in users:
        send_push_notification(user)

    # Save an image only if at least an hour has passed
    if current_time - last_image_time >= 3600:
        # todo: only do this if the light is not on
        turn_ir_on()
        time.sleep(3)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(settings.MEDIA_ROOT, "gallery", f"{timestamp}.jpg")

        frame = camera_stream.get_frame()

        cv2.imwrite(image_path, frame)
        last_image_time = current_time

        turn_ir_off()

    # Send an email only if at least a day has passed
    file_path = "last_email_sent.txt"

    # Read the existing timestamp or initialize it
    try:
        with open(file_path, "r+") as f:
            content = f.readline().strip()
            last_email_time = int(content) if content else 0  # Convert to int, default to 0 if empty
            if current_time - last_email_time >= 86400:
                try:
                    csv_file = 'newsletter_subscribers.csv'
                    with open(csv_file, mode='r') as file:
                        reader = csv.reader(file)
                        subscribers = list(reader)
                        for subscriber in subscribers:
                            email = subscriber[0]
                            encoded_email = encode_email(email)
                            if "@unibe.ch" in email:
                                base_url = "http://sedna.space.unibe.ch/voegeli"
                                unsubscribe_link = f"{base_url}/unsubscribe/{encoded_email}/"
                                email_body = (
                                    "Hoi Du!<br>"
                                    "I just came back and entered my birdhouse!<br>"
                                    f"Check me out at {base_url}<br>"
                                    "Best Regards, Your Vögeli<br><br>"
                                    f'<a href="{unsubscribe_link}">Unsubscribe</a>'
                                )
                            else:
                                base_url = "https://linusleo.synology.me"
                                unsubscribe_link = f"{base_url}/unsubscribe/{encoded_email}/"
                                email_body = (
                                    "Hoi Du!<br>"
                                    "I just came back and entered my birdhouse!<br>"
                                    f"Check me out at {base_url}<br>"
                                    "Best Regards, Your Vögeli<br><br>"
                                    f'<a href="{unsubscribe_link}">Unsubscribe</a>'
                                )

                            Voegeli.send_mail(
                                email_body,
                                subject="Vögeli Motion Alert",
                                recipients=email,
                                is_html=True,
                            )
                except FileNotFoundError:
                    pass  # File does not exist yet, no subscribers
                # Overwrite with the new timestamp
                f.seek(0)  # Move to the beginning of the file
                new_timestamp = int(current_time)
                f.write(str(new_timestamp))
                f.truncate()  # Remove any leftover content after the new write
    except FileNotFoundError:
        # If the file doesn't exist, create it and write the timestamp
        with open(file_path, "w") as f:
            new_timestamp = int(current_time)
            last_email_time = 0
            f.write(str(new_timestamp))

    print("Motion detected! Data stored.")


time.sleep(1)  # Wait for hardware to settle


# Background thread for temperature/humidity logging (runs every 60s)
def periodic_data_logger():
    # Register interrupt for motion detection (FALLING or RISING can be used)
    pir.when_motion = motion_detected_callback
    turn_off_ir_led = None
    while True:
        temperature, humidity = read_temperature_humidity()
        store_sensor_data(temperature, humidity, motion_triggered=False)
        if turn_off_ir_led is None and get_ir_led_state():
            # set turn-off to now + 5 minutes
            turn_off_ir_led = time.time() + 5 * 60
        if turn_off_ir_led is not None and turn_off_ir_led < time.time() and get_ir_led_state():
            turn_off_ir_led = None
            turn_ir_off()
        time.sleep(60)


# Start background thread
data_thread = threading.Thread(target=periodic_data_logger, daemon=True)
data_thread.start()
