# Use a Python base image (Raspberry Pi compatible)
FROM python:3.11

# Set working directory
WORKDIR /app

# Set environment variable inside Docker
ENV DOCKER_ENV=true

# Install system dependencies (including libcap-dev for python-prctl)
# Install dependencies for PiCamera and Redis
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    libcap-dev \
    libopencv-dev \
    python3-opencv \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Install picamera2 via pip (this is the correct way to install PiCamera2 on Raspberry Pi)
RUN pip install picamera2

# Copy project files
COPY backend/ /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port for Gunicorn
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "birdhouse.wsgi:application"]