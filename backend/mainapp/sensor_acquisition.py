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

from .ignore_motion import are_we_still_blocked
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
base_url = "http://cgnum.space.unibe.ch/voegeli/unsubscribe/"  # Change this to your actual unsubscribe URL


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


def motion_detected_callback():
    global last_image_time, last_email_time

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
                    email = subscriber[0]
                    unsubscribe_link = f"{base_url}{email}/"  # Dynamic unsubscribe link

                    email_body = (
                        "Hoi Du!\n"
                        "I'm moving into the birdhouse!\n"
                        "Check me out at http://cgnum.space.unibe.ch/voegeli\n"
                        "Best Regards, Your Vögeli\n\n"
                        f'<a href="{unsubscribe_link}">Unsubscribe</a>'
                    )

                    Voegeli.send_mail(
                        email_body,
                        subject="Vögeli Motion Alert",
                        recipients=email,
                        is_html=True,
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
