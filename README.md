# GStreamer Media Distributor

A powerful solution for streaming media content to multiple displays simultaneously using GStreamer and Docker. Perfect for digital signage, multi-room entertainment, or any scenario requiring synchronized media distribution.

## Features

- 🎬 **Multi-Display Streaming**: Stream to unlimited displays simultaneously
- 🌐 **Web-Based Control**: Intuitive web interface for managing streams
- � **YouTube Integration**: Stream YouTube videos directly to displays
- �🔧 **Flexible Configuration**: YAML-based configuration system
- 📊 **Real-Time Monitoring**: Live stream status and system health monitoring
- 🐳 **Docker Ready**: Complete containerized solution
- 🎵 **Audio + Video**: Full support for audio and video streaming
- 🚀 **High Performance**: Optimized GStreamer pipelines for low latency
- 🔍 **YouTube Search**: Built-in YouTube video search functionality

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Network connectivity to target displays
- Media files in supported formats (MP4, MKV, AVI, MOV, WebM)

### Setup

1. **Clone and setup the repository:**
```bash
git clone https://github.com/joshuawowk/gstreamer_distributor
cd gstreamer_distributor
./setup.sh
```

2. **Configure your displays:**
Edit `config/config.yml` and update the display endpoints:
```yaml
displays:
  endpoints:
    - name: "Living Room TV"
      ip: "192.168.1.100"
      port: 5000
      enabled: true
    - name: "Kitchen Display"
      ip: "192.168.1.101"
      port: 5001
      enabled: true
```

3. **Add your media files:**
Place your media files in the `./media` directory or update the volume mount in `docker-compose.yml`:
```yaml
volumes:
  - /path/to/your/media:/media:ro
```

4. **Start the services:**
```bash
docker-compose up -d
```

5. **Access the web interface:**
Open your browser to `http://localhost:8080`

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Control   │    │  Stream Manager  │    │    Displays     │
│    (Flask)      │◄──►│   (GStreamer)    │───►│  192.168.1.100  │
│   Port 8080     │    │   Port 8081      │    │  192.168.1.101  │
└─────────────────┘    └──────────────────┘    │  192.168.1.102  │
                                               └─────────────────┘
```

### Components

- **Web Control Interface**: Flask-based web application for stream management
- **Stream Manager**: Python service that manages GStreamer pipelines
- **GStreamer Engine**: High-performance media streaming engine
- **Configuration System**: YAML-based configuration management

## Configuration

### Main Configuration (`config/config.yml`)

```yaml
# Media library settings
media:
  library_path: "/media"
  supported_formats: [".mp4", ".mkv", ".avi", ".mov", ".webm"]

# YouTube integration settings
youtube:
  enabled: true
  default_quality: "720p"
  fallback_qualities: ["720p", "480p", "360p"]
  max_duration: 7200  # 2 hours
  cache_enabled: true
  timeout: 30

# Display configuration
displays:
  endpoints:
    - name: "Display 1"
      ip: "192.168.1.100"
      port: 5000
      enabled: true

# Streaming settings
streaming:
  video:
    codec: "x264enc"
    bitrate: 2000  # kbps
    resolution: "1920x1080"
    framerate: 30
  audio:
    codec: "lamemp3enc"
    bitrate: 128  # kbps
    samplerate: 44100

# Logging configuration
logging:
  level: "INFO"
```

### Network Configuration

- **Video streams**: UDP ports 5000-5010 (configurable per display)
- **Audio streams**: Video port + 100 (e.g., 5100-5110)
- **Web interface**: TCP port 8080
- **API server**: TCP port 8081 (internal)

## API Documentation

The stream manager provides a REST API for programmatic control:

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System health check |
| GET | `/api/streams` | List active streams |
| POST | `/api/stream/start` | Start a new stream |
| POST | `/api/stream/stop/<id>` | Stop a specific stream |
| GET | `/api/stream/<id>` | Get stream status |

### YouTube Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/youtube/validate` | Validate YouTube URL |
| POST | `/api/youtube/info` | Get video information |
| POST | `/api/youtube/search` | Search YouTube videos |
| GET | `/api/youtube/status` | YouTube integration status |
| POST | `/api/youtube/cache/clear` | Clear video cache |

### Example API Usage

**Start a local media stream:**
```bash
curl -X POST http://localhost:8081/api/stream/start \
  -H "Content-Type: application/json" \
  -d '{
    "stream_id": "local-stream-1",
    "media_source": "movies/sample.mp4",
    "displays": [
      {"name": "Display 1", "ip": "192.168.1.100", "port": 5000}
    ]
  }'
```

**Start a YouTube stream:**
```bash
curl -X POST http://localhost:8081/api/stream/start \
  -H "Content-Type: application/json" \
  -d '{
    "stream_id": "youtube-stream-1", 
    "media_source": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "displays": [
      {"name": "Display 1", "ip": "192.168.1.100", "port": 5000}
    ]
  }'
```

**Validate YouTube URL:**
```bash
curl -X POST http://localhost:8081/api/youtube/validate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

**Search YouTube videos:**
```bash
curl -X POST http://localhost:8081/api/youtube/search \
  -H "Content-Type: application/json" \
  -d '{"query": "nature documentary", "max_results": 5}'
```

## Usage

### Streaming Local Media

1. Place media files in the `./media` directory
2. Access the web interface at `http://localhost:8080`
3. Select the "Local Media" tab
4. Choose your media file from the dropdown
5. Select target displays
6. Click "Start Stream"

### Streaming YouTube Videos

1. Access the web interface at `http://localhost:8080`
2. Select the "YouTube" tab
3. **Option 1: Direct URL**
   - Paste a YouTube URL
   - Click the validate button (✓)
   - Review video information
   - Select displays and start stream
4. **Option 2: Search**
   - Click "Search YouTube"
   - Enter search terms
   - Select a video from results
   - Video will be automatically validated
   - Select displays and start stream

### Supported YouTube URLs

- Standard: `https://www.youtube.com/watch?v=VIDEO_ID`
- Short: `https://youtu.be/VIDEO_ID`
- Embed: `https://www.youtube.com/embed/VIDEO_ID`
- Mobile: `https://m.youtube.com/watch?v=VIDEO_ID`

### Quality Settings

YouTube videos are automatically streamed in the configured quality:
- **best**: Highest available quality
- **1080p, 720p, 480p, 360p**: Specific resolutions
- **worst**: Lowest quality (for bandwidth conservation)

The system automatically falls back to lower qualities if the preferred quality is unavailable.

## Troubleshooting

### YouTube Integration Issues

1. **YouTube Video Not Loading**
   - Verify the URL is valid and public
   - Check if video is available in your region
   - Some videos may have restrictions that prevent streaming
   - Age-restricted content may not be accessible

2. **Quality Issues**
   - YouTube videos respect the `default_quality` setting in config.yml
   - If preferred quality isn't available, system falls back automatically
   - Check available qualities using the validation endpoint
   - Live streams may have limited quality options

3. **Search Not Working**
   - Verify internet connectivity
   - yt-dlp may need updates for YouTube compatibility
   - Check Docker logs for YouTube API errors

4. **Stream Performance Issues**
   - YouTube streams require internet bandwidth
   - Consider lowering `default_quality` for better performance
   - Check `max_duration` setting for long videos

### General Issues

1. **Stream Not Starting**
   - Ensure GStreamer service is running
   - Check Docker logs: `docker compose logs gstreamer-server`
   - Verify network connectivity for YouTube streams
   - Confirm media files exist for local content

2. **Web Interface Not Loading**
   - Confirm services are running: `docker compose ps`
   - Check that ports 8080 and 8081 are available
   - Review web service logs: `docker compose logs web-control`

### Using GStreamer on Target Displays

```bash
# Video stream
gst-launch-1.0 udpsrc port=5000 ! \
  application/x-rtp,payload=96 ! \
  rtph264depay ! avdec_h264 ! \
  videoconvert ! autovideosink

# Audio stream  
gst-launch-1.0 udpsrc port=5100 ! \
  application/x-rtp,payload=97 ! \
  rtpmp3depay ! mpegaudioparse ! \
  avdec_mp3 ! audioconvert ! autoaudiosink
```

### Using VLC Media Player

```bash
vlc rtp://192.168.1.100:5000
```

### Using FFmpeg

```bash
ffplay rtp://192.168.1.100:5000
```

## Monitoring and Troubleshooting

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f gstreamer-server
docker-compose logs -f web-control
```

### Common Issues

1. **Streams not reaching displays**
   - Check network connectivity
   - Verify firewall settings (UDP ports 5000-5010)
   - Confirm display IP addresses in config

2. **Media files not appearing**
   - Verify volume mount paths in docker-compose.yml
   - Check file permissions
   - Ensure supported file formats

3. **High CPU usage**
   - Reduce bitrate in configuration
   - Lower video resolution
   - Limit number of simultaneous streams

## Performance Tuning

### Video Quality vs Performance

| Quality | Bitrate | CPU Usage | Network |
|---------|---------|-----------|---------|
| Low | 500 kbps | Low | Low |
| Medium | 2000 kbps | Medium | Medium |
| High | 5000 kbps | High | High |
| Ultra | 10000+ kbps | Very High | Very High |

### Optimization Tips

- Use hardware acceleration when available
- Adjust bitrate based on network capacity
- Monitor system resources during streaming
- Use appropriate codecs for your content type

## Development

### Building from Source

```bash
# Build individual services
docker-compose build gstreamer-server
docker-compose build web-control

# Build all services
docker-compose build
```

### Local Development

```bash
# Run web control locally
cd web-control
pip install -r requirements.txt
python app.py

# Run stream manager locally (requires GStreamer)
cd gstreamer-server/scripts
python stream-manager.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- Create an issue for bug reports or feature requests
- Check the troubleshooting section for common problems
- Review logs for detailed error information

## Acknowledgments

- Built with [GStreamer](https://gstreamer.freedesktop.org/)
- Web interface powered by [Flask](https://flask.palletsprojects.com/)
- Containerized with [Docker](https://www.docker.com/)
