# Use Python base image (ARM compatible for Raspberry Pi)
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy project files
COPY backend/ /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port for Gunicorn
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "birdhouse.wsgi:application"]