from django.urls import path
from .views import motion_status

urlpatterns = [
    path('status/', motion_status, name='motion_status'),
]