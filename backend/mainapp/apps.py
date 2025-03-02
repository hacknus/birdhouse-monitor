from django.apps import AppConfig
import mainapp.sensor_acquisition

class StreamappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mainapp"
