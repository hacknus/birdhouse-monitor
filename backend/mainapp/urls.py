from django.urls import path
from mainapp import views

urlpatterns = [
    path("", views.index, name="index"),
    # path("sensors", views.sensors, name="sensors"),
    # path("settings", views.settings, name="settings"),
    path("video_feed", views.video_feed, name="video_feed"),
]
