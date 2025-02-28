import threading

import RPi.GPIO as GPIO
import time

import board
import adafruit_sht4x

# Function to store the data in the database
from .models import SensorData  # Import your Django model

i2c = board.I2C()
sensor = adafruit_sht4x.SHT4x(i2c)
print("setting up SHT")
print(sensor)
# Define the GPIO pin for motion detection
MOTION_PIN = 17  # Pin 17 for motion detection

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTION_PIN, GPIO.IN)

# Function to read temperature and humidity from DHT sensor
def read_temperature_humidity():
    temperature = round(sensor.temperature, 2)
    humidity = round(sensor.relative_humidity, 2)
    if humidity is not None and temperature is not None:
        return temperature, humidity
    else:
        return None, None

# Function to check if motion is detected
def check_motion():
    return GPIO.input(MOTION_PIN)

# Collect sensor data
def collect_data():
    temperature, humidity = read_temperature_humidity()
    motion_triggered = check_motion()

    # Store this data in the database
    store_sensor_data(temperature, humidity, motion_triggered)

def store_sensor_data(temperature, humidity, motion_triggered):
    # Create a new SensorData entry in the database
    sensor_data = SensorData.objects.create(
        temperature=temperature,
        humidity=humidity,
        motion_triggered=motion_triggered
    )
    sensor_data.save()

def worker():
    # Periodically collect data (e.g., every 60 seconds)
    while True:
        collect_data()
        time.sleep(60)

# creating thread
control_thread = threading.Thread(target=worker, daemon=True)

# starting thread
control_thread.start()
