import json
import asyncio
import platform

from channels.generic.websocket import AsyncWebsocketConsumer

from threading import Thread
import io

# Detect if running on Raspberry Pi
IS_RPI = os.environ.get('DOCKER_ENV', 'false') == 'true' or platform.system() == "Linux"


class CameraConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera = None
        self.frame = None
        self.is_streaming = False

    async def connect(self):
        """Handle WebSocket connection."""
        await self.accept()
        print("WebSocket connected")

        # Start the camera if it's not already started
        if not self.is_streaming:
            self.is_streaming = True
            self.camera = None
            if IS_RPI:
                from picamera2 import Picamera2
                from picamera2.encoders import JpegEncoder
                from picamera2.outputs import FileOutput

                self.camera = Picamera2()

                self.camera.preview_configuration.size = (800, 600)
                self.camera.preview_configuration.format = "YUV420"
                self.camera.still_configuration.size = (1600, 1200)
                self.camera.still_configuration.enable_raw()
                self.camera.still_configuration.raw.size = self.camera.sensor_resolution
                self.camera.configure(self.camera.create_video_configuration(main={"size": (640, 480)}))
                self.camera.start_recording(JpegEncoder(), FileOutput(self))
            self.send_json({'status': 'Stream started'})
            # Start a separate thread to handle camera frame updates
            Thread(target=self.send_frames, daemon=True).start()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        print("WebSocket disconnected")
        if self.is_streaming:
            self.is_streaming = False
            self.camera.stop_recording()
            self.send_json({'status': 'Stream stopped'})

    async def receive(self, text_data):
        """Handle receiving data from WebSocket."""
        data = json.loads(text_data)

        # Toggle IR light if requested
        if data.get("action") == "toggle_ir":
            state = data.get("state", "off")
            self.toggle_ir(state)
            await self.send_json({"status": f"IR light turned {state}"})

    def toggle_ir(self, state):
        """Toggle IR light."""
        if IS_RPI:
            import RPi.GPIO as GPIO
            IR_PIN = 17
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(IR_PIN, GPIO.OUT)
            GPIO.output(IR_PIN, GPIO.HIGH if state == "on" else GPIO.LOW)

    def send_frames(self):
        """Send frames to WebSocket every time a new frame is captured."""
        while self.is_streaming:
            if self.frame:
                # Send frame to WebSocket clients
                self.send_json({
                    'frame': self.frame
                })
            asyncio.sleep(0.1)

    def write(self, buf):
        """Called when the camera produces a frame, send it to the WebSocket."""
        self.frame = buf
