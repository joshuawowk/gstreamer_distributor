#!/bin/bash

MEDIA_FILE="$1"
DISPLAY_IPS="$2"

# Parse display IPs (comma-separated)
IFS=',' read -ra DISPLAYS <<< "$DISPLAY_IPS"

# Build GStreamer pipeline
PIPELINE="filesrc location=/media/$MEDIA_FILE ! decodebin ! videoconvert ! tee name=t"

PORT=5000
for display in "${DISPLAYS[@]}"; do
    PIPELINE="$PIPELINE t. ! queue ! videoconvert ! x264enc bitrate=2000 ! rtpmp4vpay ! udpsink host=$display port=$PORT"
    ((PORT++))
done

echo "Starting stream: $PIPELINE"
gst-launch-1.0 $PIPELINE
