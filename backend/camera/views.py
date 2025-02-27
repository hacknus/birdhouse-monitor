import io
import os
import platform
import time
from threading import Condition, Thread
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json

from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render

from datetime import datetime

def camera_home(request):
    # Gallery images
    image_dir = os.path.join(settings.MEDIA_ROOT, 'captured_images')
    gallery_images = []
    if os.path.exists(image_dir):
        gallery_images = [f'captured_images/{f}' for f in os.listdir(image_dir) if f.endswith('.jpg')]

    return render(request, 'camera/index.html', {'gallery_images': gallery_images})

