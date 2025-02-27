import os
import platform
import random
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


def get_sensor_data(request):
    """Get temperature & humidity (real on Pi, mock on macOS)."""
    if IS_RPI:
        temp = round(sensor.temperature, 2)
        humidity = round(sensor.relative_humidity, 2)
    else:
        temp = round(random.uniform(15.0, 30.0), 2)  # Mock values
        humidity = round(random.uniform(30.0, 80.0), 2)

    return JsonResponse({"temperature": temp, "humidity": humidity})
