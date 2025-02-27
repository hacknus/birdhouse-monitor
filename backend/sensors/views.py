import os
import platform
import random
import threading
import time

from django.http import JsonResponse

# Detect if running on Raspberry Pi
IS_RPI = os.environ.get('DOCKER_ENV', 'false') == 'true' or platform.system() == "Linux"

if IS_RPI:
    import board
    import adafruit_sht4x

    i2c = board.I2C()
    sensor = adafruit_sht4x.SHT4x(i2c)
    print("setting up SHT")
    print(sensor)
else:
    sensor = None  # Mock sensor

sensor_data = {
    "temperature": None,
    "humidity": None
}
def update_sensor_data():
    global sensor_data
    while True:
        """Get temperature & humidity (real on Pi, mock on macOS)."""
        if IS_RPI:
            temp = round(sensor.temperature, 2)
            humidity = round(sensor.relative_humidity, 2)
        else:
            temp = round(random.uniform(15.0, 30.0), 2)  # Mock values
            humidity = round(random.uniform(30.0, 80.0), 2)

        sensor_data["temperature"] = temp
        sensor_data["humidity"] = humidity

        time.sleep(3)  # Update every 3 seconds


# Start the sensor data update in a separate thread
sensor_thread = threading.Thread(target=update_sensor_data)
sensor_thread.daemon = True  # Daemon thread will automatically exit when the main program exits
sensor_thread.start()


def get_sensor_data(request):
    # Return the current sensor data as a JSON response
    return JsonResponse(sensor_data)
