# apps.py
from django.apps import AppConfig

stream_client = None  # Global placeholder
tcp_client = None  # Global placeholder

class StreamappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mainapp"

    def ready(self):
        global stream_client, tcp_client  # Declare we're modifying the globals

        from .stream_client import StreamVideoClient
        from .tcp_client import TCPClient

        print("init stream client")
        stream_client = StreamVideoClient()
        print("starting stream client")
        stream_client.start()
        print("started stream client")

        print("init tcp client")
        tcp_client = TCPClient(stream_client=stream_client)
        print("starting tcp client")
        tcp_client.start()
        print("started tcp client")