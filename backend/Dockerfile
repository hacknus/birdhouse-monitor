# Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DOCKER_ENV=true

# Set work directory
WORKDIR /app

# Install dependencies
COPY backend/ /app/

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev

RUN pip install --upgrade pip && pip install -r requirements.txt

RUN mkdir -p /app/staticfiles && python manage.py collectstatic --noinput

# Collect static files
RUN python manage.py collectstatic --noinput

# Run Gunicorn server

# Expose port for Gunicorn
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "birdhouse.wsgi:application"]