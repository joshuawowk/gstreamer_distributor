#!/usr/bin/env python3
"""
YouTube Integration for GStreamer Media Distributor
Handles YouTube video URL extraction and metadata
"""

import os
import re
import logging
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import yt_dlp
from cachetools import TTLCache

class YouTubeHandler:
    def __init__(self, config: dict):
        self.config = config.get('youtube', {})
        self.logger = logging.getLogger(__name__)
        
        # Setup cache if enabled
        if self.config.get('cache_enabled', True):
            cache_duration = self.config.get('cache_duration', 3600)
            self.cache = TTLCache(maxsize=100, ttl=cache_duration)
        else:
            self.cache = None
        
        # yt-dlp options
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'format': self._get_format_selector(),
            'socket_timeout': self.config.get('timeout', 30),
        }
        
    def _get_format_selector(self) -> str:
        """Build format selector for yt-dlp based on quality preferences"""
        default_quality = self.config.get('default_quality', '720p')
        fallback_qualities = self.config.get('fallback_qualities', ['720p', '480p', '360p'])
        
        # Map quality names to format selectors
        quality_map = {
            'best': 'best[ext=mp4]',
            'worst': 'worst[ext=mp4]',
            '1080p': 'best[height<=1080][ext=mp4]',
            '720p': 'best[height<=720][ext=mp4]',
            '480p': 'best[height<=480][ext=mp4]',
            '360p': 'best[height<=360][ext=mp4]',
            '240p': 'best[height<=240][ext=mp4]'
        }
        
        # Build format string with fallbacks
        formats = []
        
        # Add preferred quality
        if default_quality in quality_map:
            formats.append(quality_map[default_quality])
        
        # Add fallback qualities
        for quality in fallback_qualities:
            if quality in quality_map and quality != default_quality:
                formats.append(quality_map[quality])
        
        # Final fallback
        formats.append('best[ext=mp4]/best')
        
        return '/'.join(formats)
    
    def is_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL"""
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+'
        ]
        
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed/)([0-9A-Za-z_-]{11})',
            r'(?:v/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information from YouTube URL"""
        if not self.is_youtube_url(url):
            return None
        
        video_id = self.extract_video_id(url)
        if not video_id:
            return None
        
        # Check cache first
        if self.cache and video_id in self.cache:
            self.logger.debug(f"Using cached info for video {video_id}")
            return self.cache[video_id]
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                # Check duration limit
                max_duration = self.config.get('max_duration', 0)
                if max_duration > 0 and info.get('duration', 0) > max_duration:
                    self.logger.warning(f"Video duration {info.get('duration')}s exceeds limit {max_duration}s")
                    return None
                
                # Extract relevant information
                video_info = {
                    'id': video_id,
                    'title': info.get('title', 'Unknown Title'),
                    'description': info.get('description', ''),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'upload_date': info.get('upload_date', ''),
                    'view_count': info.get('view_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': info.get('url', ''),
                    'formats': self._extract_format_info(info),
                    'is_live': info.get('is_live', False),
                    'original_url': url,
                    'extracted_at': time.time()
                }
                
                # Cache the result
                if self.cache:
                    self.cache[video_id] = video_info
                
                return video_info
                
        except Exception as e:
            self.logger.error(f"Error extracting YouTube video info: {e}")
            return None
    
    def _extract_format_info(self, info: dict) -> List[Dict]:
        """Extract format information for quality selection"""
        formats = []
        
        for fmt in info.get('formats', []):
            if fmt.get('vcodec') != 'none':  # Has video
                format_info = {
                    'format_id': fmt.get('format_id'),
                    'ext': fmt.get('ext'),
                    'quality': fmt.get('quality'),
                    'height': fmt.get('height'),
                    'width': fmt.get('width'),
                    'fps': fmt.get('fps'),
                    'vcodec': fmt.get('vcodec'),
                    'acodec': fmt.get('acodec'),
                    'filesize': fmt.get('filesize'),
                    'url': fmt.get('url')
                }
                formats.append(format_info)
        
        return formats
    
    def get_stream_urls(self, url: str) -> Optional[Tuple[str, str]]:
        """Get direct stream URLs for video and audio"""
        video_info = self.get_video_info(url)
        if not video_info:
            return None
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                video_url = None
                audio_url = None
                
                # Get the best format URLs
                if 'url' in info:
                    video_url = info['url']
                
                # If extract_audio is enabled, try to get separate audio stream
                if self.config.get('extract_audio', True):
                    audio_formats = [f for f in info.get('formats', []) 
                                   if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                    if audio_formats:
                        # Get best audio format
                        best_audio = max(audio_formats, 
                                       key=lambda x: x.get('abr', 0) or 0)
                        audio_url = best_audio.get('url')
                
                return video_url, audio_url
                
        except Exception as e:
            self.logger.error(f"Error getting stream URLs: {e}")
            return None
    
    def validate_url(self, url: str) -> Dict[str, any]:
        """Validate YouTube URL and return status"""
        if not url:
            return {'valid': False, 'error': 'URL is required'}
        
        if not self.is_youtube_url(url):
            return {'valid': False, 'error': 'Not a valid YouTube URL'}
        
        video_id = self.extract_video_id(url)
        if not video_id:
            return {'valid': False, 'error': 'Could not extract video ID'}
        
        # Try to get basic info
        try:
            info = self.get_video_info(url)
            if not info:
                return {'valid': False, 'error': 'Video not accessible or private'}
            
            # Check if live stream
            if info.get('is_live'):
                return {
                    'valid': True, 
                    'warning': 'Live stream detected - quality may vary',
                    'info': info
                }
            
            return {'valid': True, 'info': info}
            
        except Exception as e:
            return {'valid': False, 'error': f'Validation failed: {str(e)}'}
    
    def search_videos(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search YouTube videos (basic implementation)"""
        # Note: This is a basic implementation
        # For production, consider using YouTube Data API
        try:
            search_opts = {
                'quiet': True,
                'no_warnings': True,
                'default_search': 'ytsearch10:',
                'extract_flat': True
            }
            
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                search_results = ydl.extract_info(query, download=False)
                
                results = []
                entries = search_results.get('entries', [])[:max_results]
                
                for entry in entries:
                    result = {
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'uploader': entry.get('uploader'),
                        'duration': entry.get('duration'),
                        'view_count': entry.get('view_count'),
                        'url': f"https://www.youtube.com/watch?v={entry.get('id')}"
                    }
                    results.append(result)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def clear_cache(self):
        """Clear the video info cache"""
        if self.cache:
            self.cache.clear()
            self.logger.info("YouTube cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.cache:
            return {'enabled': False}
        
        return {
            'enabled': True,
            'size': len(self.cache),
            'max_size': self.cache.maxsize,
            'ttl': self.cache.ttl
        }
