from django.apps import AppConfig
from .tcp_client import TCPClient
from .udp_client import UDPVideoClient

tcp_client = TCPClient()  # Global instance
udp_client = UDPVideoClient()


class StreamappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mainapp"

    def ready(self):
        udp_client.start()
        tcp_client.start()
