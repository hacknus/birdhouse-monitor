import threading
import time
from datetime import datetime, timedelta, timezone

from .models import WeatherData

with open('srfmeteo.key') as f:
    CLIENT_ID = f.readline()
    CLIENT_SECRET = f.readline()

import requests


# Function to get the access token
def get_access_token():
    url = "https://api.srgssr.ch/oauth/v1/accesstoken?grant_type=client_credentials"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        # Extract access token from the response
        token_data = response.json()
        access_token = token_data.get('access_token')
        return access_token
    else:
        print("Failed to get access token:", response.status_code, response.text)
        return None


# Function to get location data for ZIP code 3012
def get_location_data(access_token, zip_code):
    url = f"https://api.srgssr.ch/srf-meteo/v2/geolocationNames?zip={zip_code}"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Process and print the location data
        location_data = response.json()
        id = location_data[0]["geolocation"]["id"]
    else:
        print("Failed to retrieve location data:", response.status_code, response.text)
    return id


def get_weather_forecast(access_token, geolocation_id):
    url = f"https://api.srgssr.ch/srf-meteo/v2/forecastpoint/{geolocation_id}"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        forecast_data = response.json()
        # Get the current time and round to the next full hour
        current_time = datetime.now(timezone.utc)  # Use UTC for consistency
        next_hour = (current_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

        # Convert to the correct ISO format with timezone offset
        next_hour_iso = next_hour.isoformat(timespec='seconds')

        # Loop through the 'hours' list to find the entry closest to the next hour
        for entry in forecast_data["hours"]:
            # Convert the 'date_time' to a datetime object
            entry_time = datetime.fromisoformat(entry["date_time"])

            # Check if the entry's time matches the next hour
            if entry_time == next_hour:
                return entry.get('TTT_C', 'N/A')
    else:
        print("Failed to retrieve weather forecast:", response.status_code, response.text)


# Function to store sensor data in the database
def store_weather_data(temperature):
    WeatherData.objects.create(
        temperature=temperature,
    )


# Background thread for temperature/humidity logging (runs every 60s)
def periodic_data_logger():
    # Register interrupt for motion detection (FALLING or RISING can be used)
    while True:
        access_token = get_access_token()  # Get the access token
        if access_token:
            id = get_location_data(access_token, 3012)  # Use the token to fetch weather data
            temperature = get_weather_forecast(access_token, id)
            store_weather_data(temperature)
        time.sleep(60)


# Start background thread
data_thread = threading.Thread(target=periodic_data_logger, daemon=True)
data_thread.start()
