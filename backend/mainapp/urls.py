from django.urls import path
from mainapp import views

urlpatterns = [
    path("", views.index, name="index"),
    path("video_feed", views.video_feed, name="video_feed"),
    path("save_image/", views.save_image, name="save_image"),  # New route
    path('gallery/', views.gallery, name='gallery'),  # Define the URL pattern
    path('making-of/', views.making_of_view, name='making_of'),
    path('trigger_ir_led/', views.trigger_ir_led, name='trigger_ir_led'),
    path('get_sensor_data/', views.get_sensor_data, name='get_sensor_data'),
    path('newsletter/', views.newsletter_view, name='newsletter'),  # Add this path
    path('newsletter/add/', views.add_email, name='add_email'),  # Add this path for adding emails
    path('newsletter/remove/', views.remove_email, name='remove_email'),  # Add this path for removing emails
]
