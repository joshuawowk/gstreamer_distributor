#!/usr/bin/env python3
"""
GStreamer Media Distributor - Stream Manager
Manages multiple GStreamer pipelines for distributed media streaming
"""

import os
import sys
import yaml
import logging
import subprocess
import threading
import signal
import time
from typing import Dict, List, Optional, Tuple
from flask import Flask, request, jsonify
import gi

gi.require_version('Gst', '1.0')
from gi import repository as Gst

# Import YouTube handler
from youtube_handler import YouTubeHandler

class StreamManager:
    def __init__(self, config_path: str = '/config/config.yml'):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.active_streams = {}
        self.running = True
        
        # Initialize YouTube handler if enabled
        if self.config.get('youtube', {}).get('enabled', True):
            self.youtube_handler = YouTubeHandler(self.config)
            self.logger.info("YouTube integration enabled")
        else:
            self.youtube_handler = None
            self.logger.info("YouTube integration disabled")
        
        # Initialize GStreamer
        Gst.init(None)
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Setup Flask API server
        self.app = Flask(__name__)
        self._setup_api_routes()
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.error(f"Config file not found: {config_path}")
            # Use default config
            return self._default_config()
        except yaml.YAMLError as e:
            logging.error(f"Error parsing config file: {e}")
            return self._default_config()
    
    def _default_config(self) -> dict:
        """Default configuration if config file is missing"""
        return {
            'media': {
                'library_path': '/media',
                'supported_formats': ['.mp4', '.mkv', '.avi', '.mov']
            },
            'youtube': {
                'enabled': True,
                'default_quality': '720p',
                'fallback_qualities': ['720p', '480p', '360p'],
                'max_duration': 7200,
                'cache_enabled': True,
                'timeout': 30
            },
            'displays': {
                'endpoints': [
                    {'name': 'Display 1', 'ip': '192.168.1.100', 'port': 5000, 'enabled': True}
                ]
            },
            'streaming': {
                'video': {'codec': 'x264enc', 'bitrate': 2000},
                'audio': {'codec': 'lamemp3enc', 'bitrate': 128},
                'network': {'protocol': 'udp', 'latency': 40}
            },
            'logging': {'level': 'INFO'}
        }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.get('logging', {}).get('level', 'INFO'))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_api_routes(self):
        """Setup Flask API routes"""
        @self.app.route('/api/health')
        def health_check():
            return jsonify({'status': 'healthy', 'active_streams': len(self.active_streams)})
        
        @self.app.route('/api/streams')
        def get_streams():
            streams = self.list_active_streams()
            return jsonify({'success': True, 'streams': streams})
        
        @self.app.route('/api/stream/start', methods=['POST'])
        def start_stream_api():
            try:
                data = request.json
                stream_id = data.get('stream_id')
                media_source = data.get('media_file') or data.get('media_source')  # Support both names
                displays = data.get('displays', [])
                
                if not stream_id or not media_source or not displays:
                    return jsonify({
                        'success': False,
                        'message': 'Missing required parameters'
                    }), 400
                
                success = self.start_stream(stream_id, media_source, displays)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Stream {stream_id} started successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'Failed to start stream {stream_id}'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"API error starting stream: {e}")
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/stream/stop/<stream_id>', methods=['POST'])
        def stop_stream_api(stream_id):
            try:
                success = self.stop_stream(stream_id)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Stream {stream_id} stopped successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'Stream {stream_id} not found or failed to stop'
                    }), 404
                    
            except Exception as e:
                self.logger.error(f"API error stopping stream: {e}")
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/stream/<stream_id>')
        def get_stream_status_api(stream_id):
            status = self.get_stream_status(stream_id)
            if status:
                return jsonify({'success': True, 'stream': status})
            else:
                return jsonify({'success': False, 'message': 'Stream not found'}), 404
        
        # YouTube-specific endpoints
        @self.app.route('/api/youtube/validate', methods=['POST'])
        def validate_youtube_url():
            try:
                if not self.youtube_handler:
                    return jsonify({
                        'success': False,
                        'message': 'YouTube integration disabled'
                    }), 503
                
                data = request.json
                url = data.get('url')
                
                if not url:
                    return jsonify({
                        'success': False,
                        'message': 'URL is required'
                    }), 400
                
                result = self.youtube_handler.validate_url(url)
                return jsonify({
                    'success': result.get('valid', False),
                    'message': result.get('error') or result.get('warning', 'Valid'),
                    'info': result.get('info')
                })
                
            except Exception as e:
                self.logger.error(f"YouTube validation error: {e}")
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/youtube/info', methods=['POST'])
        def get_youtube_info():
            try:
                if not self.youtube_handler:
                    return jsonify({
                        'success': False,
                        'message': 'YouTube integration disabled'
                    }), 503
                
                data = request.json
                url = data.get('url')
                
                if not url:
                    return jsonify({
                        'success': False,
                        'message': 'URL is required'
                    }), 400
                
                info = self.youtube_handler.get_video_info(url)
                if info:
                    return jsonify({
                        'success': True,
                        'info': info
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Could not extract video information'
                    }), 400
                    
            except Exception as e:
                self.logger.error(f"YouTube info error: {e}")
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/youtube/search', methods=['POST'])
        def search_youtube():
            try:
                if not self.youtube_handler:
                    return jsonify({
                        'success': False,
                        'message': 'YouTube integration disabled'
                    }), 503
                
                data = request.json
                query = data.get('query')
                max_results = data.get('max_results', 10)
                
                if not query:
                    return jsonify({
                        'success': False,
                        'message': 'Search query is required'
                    }), 400
                
                results = self.youtube_handler.search_videos(query, max_results)
                return jsonify({
                    'success': True,
                    'results': results
                })
                
            except Exception as e:
                self.logger.error(f"YouTube search error: {e}")
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/youtube/cache/clear', methods=['POST'])
        def clear_youtube_cache():
            try:
                if not self.youtube_handler:
                    return jsonify({
                        'success': False,
                        'message': 'YouTube integration disabled'
                    }), 503
                
                self.youtube_handler.clear_cache()
                return jsonify({
                    'success': True,
                    'message': 'Cache cleared successfully'
                })
                
            except Exception as e:
                self.logger.error(f"Cache clear error: {e}")
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/youtube/status')
        def get_youtube_status():
            try:
                if not self.youtube_handler:
                    return jsonify({
                        'enabled': False,
                        'message': 'YouTube integration disabled'
                    })
                
                cache_stats = self.youtube_handler.get_cache_stats()
                config = self.config.get('youtube', {})
                
                return jsonify({
                    'enabled': True,
                    'config': {
                        'default_quality': config.get('default_quality'),
                        'max_duration': config.get('max_duration'),
                        'timeout': config.get('timeout')
                    },
                    'cache': cache_stats
                })
                
            except Exception as e:
                self.logger.error(f"YouTube status error: {e}")
                return jsonify({
                    'enabled': False,
                    'error': str(e)
                })
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.stop_all_streams()
        
    def get_enabled_displays(self) -> List[dict]:
        """Get list of enabled display endpoints"""
        return [
            display for display in self.config['displays']['endpoints'] 
            if display.get('enabled', True)
        ]
    
    def build_gstreamer_pipeline(self, media_source: str, displays: List[dict]) -> str:
        """Build GStreamer pipeline for multiple displays"""
        if not displays:
            raise ValueError("No displays provided")
        
        # Determine if source is YouTube URL or local file
        is_youtube = (self.youtube_handler and 
                     self.youtube_handler.is_youtube_url(media_source))
        
        if is_youtube:
            return self._build_youtube_pipeline(media_source, displays)
        else:
            return self._build_local_file_pipeline(media_source, displays)
    
    def _build_local_file_pipeline(self, media_file: str, displays: List[dict]) -> str:
        """Build GStreamer pipeline for local media files"""
        # Get media file path
        media_path = os.path.join(self.config['media']['library_path'], media_file)
        if not os.path.exists(media_path):
            raise FileNotFoundError(f"Media file not found: {media_path}")
        
        # Video settings
        video_settings = self.config['streaming']['video']
        audio_settings = self.config['streaming']['audio']
        
        # Build pipeline components
        pipeline_parts = [
            f'filesrc location="{media_path}"',
            '! decodebin name=dec'
        ]
        
        return self._build_common_pipeline(pipeline_parts, displays, video_settings, audio_settings)
    
    def _build_youtube_pipeline(self, youtube_url: str, displays: List[dict]) -> str:
        """Build GStreamer pipeline for YouTube videos"""
        if not self.youtube_handler:
            raise ValueError("YouTube integration not enabled")
        
        # Get stream URLs
        stream_urls = self.youtube_handler.get_stream_urls(youtube_url)
        if not stream_urls:
            raise ValueError("Could not extract YouTube stream URLs")
        
        video_url, audio_url = stream_urls
        
        # Video settings
        video_settings = self.config['streaming']['video']
        audio_settings = self.config['streaming']['audio']
        
        if audio_url and self.config.get('youtube', {}).get('extract_audio', True):
            # Separate video and audio streams
            pipeline_parts = [
                f'souphttpsrc location="{video_url}" ! decodebin name=videodec',
                f'souphttpsrc location="{audio_url}" ! decodebin name=audiodec'
            ]
        else:
            # Single stream with video and audio
            pipeline_parts = [
                f'souphttpsrc location="{video_url}"',
                '! decodebin name=dec'
            ]
        
        return self._build_common_pipeline(pipeline_parts, displays, video_settings, audio_settings)
    
    def _build_common_pipeline(self, source_parts: List[str], displays: List[dict], 
                              video_settings: dict, audio_settings: dict) -> str:
        """Build common pipeline parts for video/audio distribution"""
        
        # Video branch with tee for multiple outputs
        video_branch = [
            'dec.',
            '! queue',
            '! videoconvert',
            '! videoscale',
            f'! video/x-raw,width=1920,height=1080',
            '! tee name=video_tee'
        ]
        
        # Audio branch with tee for multiple outputs  
        audio_branch = [
            'dec.',
            '! queue',
            '! audioconvert',
            '! audioresample', 
            '! tee name=audio_tee'
        ]
        
        # Add video outputs for each display
        video_outputs = []
        audio_outputs = []
        
        for i, display in enumerate(displays):
            # Video output
            video_out = [
                'video_tee.',
                '! queue',
                '! videoconvert',
                f'! {video_settings["codec"]} bitrate={video_settings["bitrate"]}',
                '! rtph264pay config-interval=1 pt=96',
                f'! udpsink host={display["ip"]} port={display["port"]}'
            ]
            video_outputs.append(' '.join(video_out))
            
            # Audio output (port + 100 for audio)
            audio_port = display["port"] + 100
            audio_out = [
                'audio_tee.',
                '! queue',
                '! audioconvert',
                f'! {audio_settings["codec"]} bitrate={audio_settings["bitrate"]}',
                '! rtpmpapay pt=97',
                f'! udpsink host={display["ip"]} port={audio_port}'
            ]
            audio_outputs.append(' '.join(audio_out))
        
        # Combine all pipeline parts
        full_pipeline = (
            ' '.join(source_parts) + ' ' +
            ' '.join(video_branch) + ' ' +
            ' '.join(audio_branch) + ' ' +
            ' '.join(video_outputs) + ' ' +
            ' '.join(audio_outputs)
        )
        
        return full_pipeline
    
    def start_stream(self, stream_id: str, media_source: str, displays: List[dict]) -> bool:
        """Start a new stream"""
        try:
            if stream_id in self.active_streams:
                self.logger.warning(f"Stream {stream_id} already exists")
                return False
                
            pipeline_str = self.build_gstreamer_pipeline(media_source, displays)
            self.logger.info(f"Starting stream {stream_id}: {media_source}")
            self.logger.debug(f"Pipeline: {pipeline_str}")
            
            # Start GStreamer process
            process = subprocess.Popen(
                ['gst-launch-1.0'] + pipeline_str.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Determine source type for metadata
            is_youtube = (self.youtube_handler and 
                         self.youtube_handler.is_youtube_url(media_source))
            
            self.active_streams[stream_id] = {
                'process': process,
                'media_source': media_source,
                'source_type': 'youtube' if is_youtube else 'local',
                'displays': displays,
                'start_time': time.time()
            }
            
            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_stream,
                args=(stream_id,),
                daemon=True
            )
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start stream {stream_id}: {e}")
            return False
    
    def stop_stream(self, stream_id: str) -> bool:
        """Stop a specific stream"""
        if stream_id not in self.active_streams:
            self.logger.warning(f"Stream {stream_id} not found")
            return False
            
        try:
            stream_info = self.active_streams[stream_id]
            process = stream_info['process']
            
            # Terminate process gracefully
            process.terminate()
            
            # Wait for termination with timeout
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Force killing stream {stream_id}")
                process.kill()
                process.wait()
            
            del self.active_streams[stream_id]
            self.logger.info(f"Stopped stream {stream_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop stream {stream_id}: {e}")
            return False
    
    def stop_all_streams(self):
        """Stop all active streams"""
        stream_ids = list(self.active_streams.keys())
        for stream_id in stream_ids:
            self.stop_stream(stream_id)
    
    def _monitor_stream(self, stream_id: str):
        """Monitor stream process"""
        if stream_id not in self.active_streams:
            return
            
        stream_info = self.active_streams[stream_id]
        process = stream_info['process']
        
        # Read stderr for GStreamer messages
        while process.poll() is None and self.running:
            try:
                line = process.stderr.readline()
                if line:
                    # Log important GStreamer messages
                    if 'ERROR' in line or 'WARNING' in line:
                        self.logger.warning(f"Stream {stream_id}: {line.strip()}")
                    elif 'INFO' in line:
                        self.logger.debug(f"Stream {stream_id}: {line.strip()}")
            except Exception as e:
                self.logger.error(f"Error monitoring stream {stream_id}: {e}")
                break
        
        # Process ended
        if stream_id in self.active_streams:
            return_code = process.poll()
            if return_code != 0:
                self.logger.error(f"Stream {stream_id} ended with error code {return_code}")
            else:
                self.logger.info(f"Stream {stream_id} ended normally")
            
            # Clean up
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
    
    def get_stream_status(self, stream_id: str) -> Optional[dict]:
        """Get status of a specific stream"""
        if stream_id not in self.active_streams:
            return None
            
        stream_info = self.active_streams[stream_id]
        process = stream_info['process']
        
        return {
            'stream_id': stream_id,
            'media_source': stream_info['media_source'],
            'source_type': stream_info['source_type'],
            'displays': len(stream_info['displays']),
            'running': process.poll() is None,
            'uptime': time.time() - stream_info['start_time'],
            'pid': process.pid
        }
    
    def list_active_streams(self) -> List[dict]:
        """List all active streams"""
        return [
            self.get_stream_status(stream_id) 
            for stream_id in self.active_streams.keys()
        ]
    
    def run_api_server(self):
        """Run Flask API server in a separate thread"""
        self.app.run(host='0.0.0.0', port=8081, debug=False, use_reloader=False)
    
    def run(self):
        """Main run loop"""
        self.logger.info("GStreamer Media Distributor started")
        self.logger.info(f"Monitoring {len(self.get_enabled_displays())} enabled displays")
        
        # Start API server in background thread
        api_thread = threading.Thread(target=self.run_api_server, daemon=True)
        api_thread.start()
        self.logger.info("API server started on port 8081")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        finally:
            self.stop_all_streams()
            self.logger.info("GStreamer Media Distributor stopped")

if __name__ == '__main__':
    # Check for config file argument
    config_path = sys.argv[1] if len(sys.argv) > 1 else '/config/config.yml'
    
    # Create and run stream manager
    manager = StreamManager(config_path)
    manager.run()
