FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    Flask \
    PyYAML \
    requests

WORKDIR /app

# Copy application files
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

# Create volume mount points
VOLUME ["/media-library", "/config"]

# Expose web interface port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

CMD ["python", "app.py"]
