# camera/urls.py
from django.urls import path
from . import views

app_name = 'camera'

urlpatterns = [
    path('', views.camera_home, name='camera_home'),  # Regular HTTP route
    # You can add other regular routes here if needed
]