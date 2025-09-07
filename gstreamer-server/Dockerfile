FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-rtsp \
    python3 \
    python3-pip \
    python3-dev \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    PyYAML \
    Flask \
    requests \
    yt-dlp \
    cachetools

WORKDIR /app
COPY scripts/ ./scripts/
RUN chmod +x scripts/*.sh

# Expose ports for streaming and API
EXPOSE 5000-5010/udp
EXPOSE 8081

# Create volume mount points
VOLUME ["/media", "/config"]

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GST_DEBUG=2

CMD ["python3", "scripts/stream-manager.py"]
