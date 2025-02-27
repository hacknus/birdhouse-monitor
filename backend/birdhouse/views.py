import os
import platform
import time

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render


def home(request):
    return HttpResponse(
        "<h1>Welcome to the Birdhouse Monitor!</h1><p>Go to <a href='/camera/'>/camera/</a> to view the camera.</p>")

def camera_view(request):
    return render(request, 'camera/index.html')