# Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev

RUN pip install --upgrade pip && pip install -r requirements.txt
# Copy project files
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run Gunicorn server
CMD ["gunicorn", "birdhouse.wsgi:application", "--bind", "0.0.0.0:8000"]