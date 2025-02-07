import os
import random
import platform
from django.http import JsonResponse

# Detect if running on Raspberry Pi
IS_RPI = platform.system() == "Linux" and os.path.exists("/sys/firmware/devicetree/base/model")

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