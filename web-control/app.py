#!/usr/bin/env python3
"""
GStreamer Media Distributor - Web Control Interface
Flask web application for managing media streams
"""

from flask import Flask, render_template, request, jsonify
import os
import requests
import yaml
import logging
import uuid
import re
from typing import List, Dict, Optional

app = Flask(__name__)

# Configuration
CONFIG_PATH = '/config/config.yml'
STREAM_MANAGER_URL = 'http://gstreamer-server:8081'  # Internal Docker communication

class WebController:
    def __init__(self):
        self.config = self._load_config()
        self._setup_logging()
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(CONFIG_PATH, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.warning(f"Config file not found: {CONFIG_PATH}")
            return self._default_config()
        except yaml.YAMLError as e:
            logging.error(f"Error parsing config file: {e}")
            return self._default_config()
    
    def _default_config(self) -> dict:
        """Default configuration"""
        return {
            'media': {
                'library_path': '/media-library',
                'supported_formats': ['.mp4', '.mkv', '.avi', '.mov', '.webm']
            },
            'youtube': {
                'enabled': True,
                'default_quality': '720p',
                'max_duration': 7200
            },
            'displays': {
                'endpoints': [
                    {'name': 'Display 1', 'ip': '192.168.1.100', 'port': 5000, 'enabled': True}
                ]
            },
            'web': {
                'host': '0.0.0.0',
                'port': 8080,
                'debug': False
            }
        }
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

# Initialize controller
controller = WebController()

@app.route('/')
def index():
    """Main dashboard page"""
    media_files = get_media_files()
    youtube_enabled = controller.config.get('youtube', {}).get('enabled', True)
    return render_template('index.html', 
                         media_files=media_files, 
                         youtube_enabled=youtube_enabled)

@app.route('/api/displays')
def get_displays():
    """Get list of available displays"""
    try:
        displays = controller.config.get('displays', {}).get('endpoints', [])
        return jsonify({
            'success': True,
            'displays': displays
        })
    except Exception as e:
        logging.error(f"Error getting displays: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/media')
def get_media():
    """Get list of available media files"""
    try:
        media_files = get_media_files()
        return jsonify({
            'success': True,
            'media_files': media_files
        })
    except Exception as e:
        logging.error(f"Error getting media files: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/streams')
def get_active_streams():
    """Get list of active streams"""
    try:
        # Try to communicate with stream manager
        try:
            response = requests.get(f'{STREAM_MANAGER_URL}/api/streams', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return jsonify({
                    'success': True,
                    'streams': data.get('streams', [])
                })
        except requests.RequestException:
            # Stream manager not available, return empty list
            pass
        
        return jsonify({
            'success': True,
            'streams': []
        })
    except Exception as e:
        logging.error(f"Error getting streams: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/stream/start', methods=['POST'])
def start_stream():
    """Start a new media stream"""
    try:
        data = request.json
        media_source = data.get('file') or data.get('url')  # Support both file and URL
        displays = data.get('displays', [])
        source_type = data.get('type', 'local')  # 'local' or 'youtube'
        
        if not media_source:
            return jsonify({
                'success': False,
                'message': 'Media source is required'
            }), 400
        
        if not displays:
            return jsonify({
                'success': False, 
                'message': 'At least one display is required'
            }), 400
        
        # Generate unique stream ID
        stream_id = str(uuid.uuid4())[:8]
        
        # Try to communicate with stream manager
        try:
            stream_data = {
                'stream_id': stream_id,
                'media_source': media_source,
                'displays': displays
            }
            
            response = requests.post(
                f'{STREAM_MANAGER_URL}/api/stream/start',
                json=stream_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return jsonify({
                    'success': result.get('success', False),
                    'message': result.get('message', 'Stream started'),
                    'stream_id': stream_id,
                    'source_type': source_type
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to start stream on server'
                }), 500
        
        except requests.RequestException as e:
            logging.error(f"Error communicating with stream manager: {e}")
            return jsonify({
                'success': False,
                'message': 'Stream manager unavailable'
            }), 503
        
    except Exception as e:
        logging.error(f"Error starting stream: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/stream/stop/<stream_id>', methods=['POST'])
def stop_stream(stream_id):
    """Stop a specific stream"""
    try:
        # Try to communicate with stream manager
        try:
            response = requests.post(
                f'{STREAM_MANAGER_URL}/api/stream/stop/{stream_id}',
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                return jsonify({
                    'success': result.get('success', False),
                    'message': result.get('message', 'Stream stopped')
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to stop stream'
                }), 500
        
        except requests.RequestException as e:
            logging.error(f"Error communicating with stream manager: {e}")
            return jsonify({
                'success': False,
                'message': 'Stream manager unavailable'
            }), 503
        
    except Exception as e:
        logging.error(f"Error stopping stream: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/status')
def get_system_status():
    """Get system status"""
    try:
        # Check stream manager health
        stream_manager_healthy = False
        try:
            response = requests.get(f'{STREAM_MANAGER_URL}/api/health', timeout=3)
            stream_manager_healthy = response.status_code == 200
        except requests.RequestException:
            pass
        
        # Check media directory
        media_dir = controller.config.get('media', {}).get('library_path', '/media-library')
        media_accessible = os.path.exists(media_dir)
        
        # Determine overall status
        if stream_manager_healthy and media_accessible:
            status = 'OK'
        elif media_accessible:
            status = 'DEGRADED'
        else:
            status = 'ERROR'
        
        return jsonify({
            'success': True,
            'status': status,
            'components': {
                'stream_manager': stream_manager_healthy,
                'media_library': media_accessible
            }
        })
    
    except Exception as e:
        logging.error(f"Error getting system status: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# YouTube-specific endpoints
@app.route('/api/youtube/validate', methods=['POST'])
def validate_youtube_url():
    """Validate YouTube URL"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({
                'success': False,
                'message': 'URL is required'
            }), 400
        
        # Forward to stream manager
        response = requests.post(
            f'{STREAM_MANAGER_URL}/api/youtube/validate',
            json={'url': url},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({
                'success': False,
                'message': 'YouTube validation failed'
            }), response.status_code
        
    except requests.RequestException as e:
        logging.error(f"Error validating YouTube URL: {e}")
        return jsonify({
            'success': False,
            'message': 'Stream manager unavailable'
        }), 503
    except Exception as e:
        logging.error(f"Error validating YouTube URL: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/youtube/info', methods=['POST'])
def get_youtube_info():
    """Get YouTube video information"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({
                'success': False,
                'message': 'URL is required'
            }), 400
        
        # Forward to stream manager
        response = requests.post(
            f'{STREAM_MANAGER_URL}/api/youtube/info',
            json={'url': url},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to get YouTube info'
            }), response.status_code
        
    except requests.RequestException as e:
        logging.error(f"Error getting YouTube info: {e}")
        return jsonify({
            'success': False,
            'message': 'Stream manager unavailable'
        }), 503
    except Exception as e:
        logging.error(f"Error getting YouTube info: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/youtube/search', methods=['POST'])
def search_youtube():
    """Search YouTube videos"""
    try:
        data = request.json
        query = data.get('query')
        max_results = data.get('max_results', 10)
        
        if not query:
            return jsonify({
                'success': False,
                'message': 'Search query is required'
            }), 400
        
        # Forward to stream manager
        response = requests.post(
            f'{STREAM_MANAGER_URL}/api/youtube/search',
            json={'query': query, 'max_results': max_results},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({
                'success': False,
                'message': 'YouTube search failed'
            }), response.status_code
        
    except requests.RequestException as e:
        logging.error(f"Error searching YouTube: {e}")
        return jsonify({
            'success': False,
            'message': 'Stream manager unavailable'
        }), 503
    except Exception as e:
        logging.error(f"Error searching YouTube: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/youtube/status')
def get_youtube_status():
    """Get YouTube integration status"""
    try:
        # Check local config first
        youtube_config = controller.config.get('youtube', {})
        if not youtube_config.get('enabled', True):
            return jsonify({
                'enabled': False,
                'message': 'YouTube integration disabled in config'
            })
        
        # Forward to stream manager for detailed status
        response = requests.get(
            f'{STREAM_MANAGER_URL}/api/youtube/status',
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({
                'enabled': False,
                'message': 'Stream manager unavailable'
            })
        
    except requests.RequestException:
        return jsonify({
            'enabled': False,
            'message': 'Stream manager unavailable'
        })
    except Exception as e:
        logging.error(f"Error getting YouTube status: {e}")
        return jsonify({
            'enabled': False,
            'error': str(e)
        })

def get_media_files() -> List[str]:
    """Scan media directory and return available files"""
    media_files = []
    media_dir = controller.config.get('media', {}).get('library_path', '/media-library')
    supported_formats = controller.config.get('media', {}).get('supported_formats', ['.mp4', '.mkv', '.avi', '.mov'])
    
    if os.path.exists(media_dir):
        for root, dirs, files in os.walk(media_dir):
            for file in files:
                if any(file.lower().endswith(fmt) for fmt in supported_formats):
                    relative_path = os.path.relpath(os.path.join(root, file), media_dir)
                    media_files.append(relative_path)
    
    return sorted(media_files)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    config = controller.config.get('web', {})
    app.run(
        host=config.get('host', '0.0.0.0'),
        port=config.get('port', 8080),
        debug=config.get('debug', False)
    )
