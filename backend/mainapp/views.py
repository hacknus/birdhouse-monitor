import json
import time
import datetime
import cv2
import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render

from picamera2 import Picamera2

# init camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (800, 600)}))
picam2.start()


def img_generator():
    while True:
        frame = picam2.capture_array()
        frame = frame[:, :, :-1]
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        # compression
        ret, jpeg = cv2.imencode(".jpg", frame)

        yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n\r\n"
        )


def video_feed(request):
    return StreamingHttpResponse(
        img_generator(), content_type="multipart/x-mixed-replace;boundary=frame"
    )


def index(request):
    return render(request, "index.html")

def save_image(request):
    if request.method == "POST":
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(settings.MEDIA_ROOT, "gallery", f"{timestamp}.jpg")

        frame = picam2.capture_array()
        frame = frame[:, :, :-1]
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        cv2.imwrite(image_path, frame)

        return JsonResponse({"message": "Image saved!", "image_url": f"/media/gallery/{timestamp}.jpg"})

    return JsonResponse({"error": "Invalid request"}, status=400)

def gallery(request):
    image_dir = os.path.join(settings.MEDIA_URL, "gallery/")
    images = [{"url": f"{image_dir}{image}"} for image in os.listdir(os.path.join(settings.MEDIA_ROOT, "gallery"))]

    return render(request, "gallery.html", {"images": images})