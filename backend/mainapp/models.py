from django.db import models


class SensorData(models.Model):
    temperature = models.FloatField()
    humidity = models.FloatField()
    motion_triggered = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    number_of_visitors = models.IntegerField()

    def __str__(self):
        return (f"{self.timestamp}, {self.temperature}°C, {self.humidity}%, Motion: {self.motion_triggered},"
                f"Visitors: {self.number_of_visitors}")


class WeatherData(models.Model):
    temperature = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp}, {self.temperature}°C"
