#!/bin/bash

# GStreamer Media Distributor Setup Script
# This script sets up the environment for the media distributor

set -e

echo "🎬 GStreamer Media Distributor Setup"
echo "====================================="

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check for Docker Compose (v2 or v1)
COMPOSE_CMD=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p media config

# Copy example config if config.yml doesn't exist
if [ ! -f "config/config.yml" ]; then
    if [ -f "config/config.example.yml" ]; then
        echo "📄 Creating config.yml from example..."
        cp config/config.example.yml config/config.yml
        echo "⚠️  Please edit config/config.yml to configure your displays and settings"
    else
        echo "❌ config.example.yml not found"
        exit 1
    fi
else
    echo "✅ config.yml already exists"
fi

# Check if media directory has content
if [ -z "$(ls -A media 2>/dev/null)" ]; then
    echo "📺 Media directory is empty"
    echo "   Place your media files (.mp4, .mkv, .avi, .mov) in the ./media directory"
    echo "   You can also update the docker-compose.yml to mount your existing media directory"
fi

# Make sure scripts are executable
echo "🔧 Setting script permissions..."
chmod +x gstreamer-server/scripts/*.sh 2>/dev/null || true

# Validate docker-compose.yml
echo "🔍 Validating Docker Compose configuration..."
if $COMPOSE_CMD config > /dev/null 2>&1; then
    echo "✅ Docker Compose configuration is valid"
else
    echo "❌ Docker Compose configuration has errors"
    $COMPOSE_CMD config
    exit 1
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config/config.yml to configure your display endpoints"
echo "2. Place your media files in the ./media directory (or update docker-compose.yml)"
echo "3. Run: $COMPOSE_CMD up -d"
echo "4. Access the web interface at: http://localhost:8080"
echo ""
echo "For more information, see README.md"
