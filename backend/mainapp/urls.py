from django.urls import path
from mainapp import views

urlpatterns = [
    path("", views.index, name="index"),
    # path("sensors", views.sensors, name="sensors"),
    # path("settings", views.settings, name="settings"),
    path("video_feed", views.video_feed, name="video_feed"),
    path("save_image/", views.save_image, name="save_image"),  # New route
    path('gallery/', views.gallery, name='gallery'),  # Define the URL pattern
    path('trigger_ir_led/', views.trigger_ir_led, name='trigger_ir_led'),
]
