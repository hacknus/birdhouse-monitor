# Use a Python base image (Raspberry Pi compatible)
FROM python:3.11

# Set working directory
WORKDIR /app

# Set environment variable inside Docker
ENV DOCKER_ENV=true

RUN apt update && apt install -y --no-install-recommends gnupg

RUN echo "deb http://archive.raspberrypi.org/debian/ bookworm main" > /etc/apt/sources.list.d/raspi.list \
  && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 82B129927FA3303E

RUN apt update && apt -y upgrade

# Install system dependencies (including libcap-dev for python-prctl)
# Install dependencies for PiCamera and Redis
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    libcap-dev \
    libopencv-dev \
    python3-picamera2 \
    python3-libcamera \
    python3-opencv \
    redis-server \
    libcamera-dev \
    libcamera-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY backend/ /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/staticfiles && python manage.py collectstatic --noinput

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port for Gunicorn
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "birdhouse.wsgi:application"]