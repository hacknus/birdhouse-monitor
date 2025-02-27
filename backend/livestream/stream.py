# livestream/stream.py

import io
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput


class CameraStream:
    def __init__(self):
        # Initialize the camera
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_video_configuration(main={"size": (640, 480)}))
        self.camera.start_recording(JpegEncoder(), FileOutput(self))

    def get_frame(self):
        """Get a single frame as JPEG"""
        stream = io.BytesIO()
        self.camera.capture(stream, format='jpeg')
        return stream.getvalue()

    def gen(self):
        """Stream frames endlessly"""
        while True:
            frame = self.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')