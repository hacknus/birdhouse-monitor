import json
import time
import datetime
import cv2
import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render

from picamera2 import Picamera2
from ultralytics import YOLO

# Load a YOLOv8n PyTorch model
model = YOLO('yolov8n.pt')

# Export the model to NCNN format
model.export(format='ncnn')  # creates 'yolov8n_ncnn_model'

# Load the exported NCNN model
ncnn_model = YOLO('yolov8n_ncnn_model')

# init camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (128, 128)}))
picam2.start()


def img_generator():
    while True:
        frame = picam2.capture_array()
        frame = frame[:, :, :-1]
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        # Run inference
        frame = ncnn_model(frame)[0]

        frame = cv2.resize(frame.plot(), (512, 512), interpolation=cv2.INTER_CUBIC)

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

