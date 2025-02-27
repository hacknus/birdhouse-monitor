import time

from flask import Flask, Response
from picamera2 import Picamera2
import io

app = Flask(__name__)
camera = Picamera2()
camera.preview_configuration.size = (800, 600)
camera.preview_configuration.format = "YUV420"
camera.still_configuration.size = (1600, 1200)
camera.still_configuration.enable_raw()
camera.still_configuration.raw.size = camera.sensor_resolution

camera.start("preview", show_preview=False)
time.sleep(2)

def generate():
    stream = io.BytesIO()
    while True:
        camera.capture_file(stream, format='jpeg')
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + stream.getvalue() + b'\r\n')
        stream.seek(0)
        stream.truncate()

@app.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)