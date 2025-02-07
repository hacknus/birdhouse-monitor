from django.urls import path
from .views import get_sensor_data

urlpatterns = [
    path('data/', get_sensor_data, name='sensor_data'),
]