import os
import platform
import random
from django.http import JsonResponse

# Detect if running on Raspberry Pi
IS_RPI = os.environ.get('DOCKER_ENV', 'false') == 'true' and platform.system() == "Linux"

if IS_RPI:
    import board
    import adafruit_sht4x
    i2c = board.I2C()
    sensor = adafruit_sht4x.SHT4x(i2c)
else:
    sensor = None  # Mock sensor

def get_sensor_data(request):
    """Get temperature & humidity (real on Pi, mock on macOS)."""
    if IS_RPI:
        temp = sensor.temperature
        humidity = sensor.relative_humidity
    else:
        temp = round(random.uniform(15.0, 30.0), 2)  # Mock values
        humidity = round(random.uniform(30.0, 80.0), 2)

    return JsonResponse({"temperature": temp, "humidity": humidity})