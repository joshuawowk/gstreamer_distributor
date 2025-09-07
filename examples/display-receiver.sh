#!/bin/bash

# GStreamer Media Distributor - Display Receiver Example
# This script demonstrates how to receive streams on display endpoints

# Configuration
VIDEO_PORT=${1:-5000}
AUDIO_PORT=$((VIDEO_PORT + 100))
DISPLAY_MODE=${2:-window}  # window, fullscreen, or test

echo "🎬 GStreamer Display Receiver"
echo "============================="
echo "Video Port: $VIDEO_PORT"
echo "Audio Port: $AUDIO_PORT"
echo "Display Mode: $DISPLAY_MODE"
echo ""

# Check if GStreamer is installed
if ! command -v gst-launch-1.0 &> /dev/null; then
    echo "❌ GStreamer is not installed"
    echo "   Ubuntu/Debian: sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-good"
    echo "   macOS: brew install gstreamer gst-plugins-good"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping receiver..."
    jobs -p | xargs -r kill
    exit 0
}

# Setup signal handlers
trap cleanup SIGINT SIGTERM

echo "▶️  Starting video receiver on port $VIDEO_PORT..."

# Video pipeline based on display mode
case $DISPLAY_MODE in
    "fullscreen")
        VIDEO_SINK="videoconvert ! autovideosink fullscreen=true"
        ;;
    "test")
        VIDEO_SINK="videoconvert ! ximagesink"
        ;;
    *)
        VIDEO_SINK="videoconvert ! autovideosink"
        ;;
esac

# Start video receiver
gst-launch-1.0 \
    udpsrc port=$VIDEO_PORT ! \
    application/x-rtp,payload=96 ! \
    rtph264depay ! \
    avdec_h264 ! \
    $VIDEO_SINK &

VIDEO_PID=$!

echo "▶️  Starting audio receiver on port $AUDIO_PORT..."

# Start audio receiver
gst-launch-1.0 \
    udpsrc port=$AUDIO_PORT ! \
    application/x-rtp,payload=97 ! \
    rtpmp3depay ! \
    mpegaudioparse ! \
    avdec_mp3 ! \
    audioconvert ! \
    autoaudiosink &

AUDIO_PID=$!

echo ""
echo "✅ Receiver started successfully!"
echo "   Video PID: $VIDEO_PID"
echo "   Audio PID: $AUDIO_PID"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for processes
wait
