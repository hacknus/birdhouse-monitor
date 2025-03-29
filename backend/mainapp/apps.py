# apps.py
from django.apps import AppConfig

udp_client = None  # Global placeholder
tcp_client = None  # Global placeholder

class StreamappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mainapp"

    def ready(self):
        global udp_client, tcp_client  # Declare we're modifying the globals

        from .udp_client import UDPVideoClient
        from .tcp_client import TCPClient

        print("init udp client")
        udp_client = UDPVideoClient()
        print("starting udp client")
        udp_client.start()
        print("started udp client")

        print("init tcp client")
        tcp_client = TCPClient(udp_client=udp_client)
        print("starting tcp client")
        tcp_client.start()
        print("started tcp client")