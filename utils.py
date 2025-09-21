# utils.py
import os
import re
import json
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    # Remove invalid characters for Windows and Unix
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Limit length to prevent filesystem issues
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized or 'untitled'

def format_bytes(bytes_value):
    """Convert bytes to human readable format"""
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    
    while bytes_value >= 1024 and unit_index < len(units) - 1:
        bytes_value /= 1024.0
        unit_index += 1
    
    return f"{bytes_value:.1f} {units[unit_index]}"

def format_duration(seconds):
    """Convert seconds to human readable duration"""
    if not seconds or seconds < 0:
        return '0:00'
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"

def is_valid_youtube_url(url):
    """Validate YouTube URL"""
    if not url or not isinstance(url, str):
        return False
    
    patterns = [
        r'^https?://(www\.)?(youtube\.com/watch\?v=[\w-]+)',
        r'^https?://(www\.)?youtu\.be/[\w-]+',
        r'^https?://(www\.)?youtube\.com/playlist\?list=[\w-]+',
        r'^https?://(www\.)?youtube\.com/embed/[\w-]+',
        r'^https?://(www\.)?youtube\.com/v/[\w-]+'
    ]
    
    return any(re.match(pattern, url.strip()) for pattern in patterns)

def cleanup_old_files(download_folder, days=7):
    """Remove files older than specified days"""
    try:
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        removed_count = 0
        
        for filename in os.listdir(download_folder):
            filepath = os.path.join(download_folder, filename)
            
            if os.path.isfile(filepath):
                file_time = os.path.getmtime(filepath)
                if file_time < cutoff_time:
                    try:
                        os.remove(filepath)
                        removed_count += 1
                    except OSError:
                        pass  # File might be in use or permission denied
        
        return removed_count
    except Exception:
        return 0

def get_file_size(filepath):
    """Get file size safely"""
    try:
        return os.path.getsize(filepath)
    except (OSError, IOError):
        return 0

def validate_json_request(required_fields=None):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(max_requests=10, window_minutes=1):
    """Simple rate limiting decorator"""
    requests = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = datetime.now()
            
            # Clean old requests
            cutoff_time = current_time - timedelta(minutes=window_minutes)
            if client_ip in requests:
                requests[client_ip] = [
                    req_time for req_time in requests[client_ip] 
                    if req_time > cutoff_time
                ]
            
            # Check rate limit
            if client_ip not in requests:
                requests[client_ip] = []
            
            if len(requests[client_ip]) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded. Please try again later.'
                }), 429
            
            requests[client_ip].append(current_time)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def safe_json_load(filepath, default=None):
    """Safely load JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return default or []

def safe_json_save(filepath, data):
    """Safely save JSON file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write to temporary file first, then rename for atomicity
        temp_filepath = filepath + '.tmp'
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        os.replace(temp_filepath, filepath)
        return True
    except (IOError, OSError):
        # Clean up temp file if it exists
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except OSError:
                pass
        return False

def get_video_info_safe(url):
    """Safely get video information with error handling"""
    try:
        from pytube import YouTube, Playlist
        
        if 'playlist' in url:
            playlist = Playlist(url)
            return {
                'type': 'playlist',
                'title': playlist.title or 'Unknown Playlist',
                'video_count': len(list(playlist.video_urls)),
                'description': f"Playlist with {len(list(playlist.video_urls))} videos"
            }
        else:
            yt = YouTube(url)
            streams = yt.streams.filter(progressive=True, file_extension='mp4')
            available_qualities = sorted(list(set([
                stream.resolution for stream in streams if stream.resolution
            ])), key=lambda x: int(x.replace('p', '')), reverse=True)
            
            return {
                'type': 'video',
                'title': yt.title or 'Unknown Title',
                'thumbnail': yt.thumbnail_url,
                'duration': yt.length or 0,
                'description': (yt.description[:200] + '...') if yt.description and len(yt.description) > 200 else (yt.description or ''),
                'available_qualities': available_qualities
            }
    except Exception as e:
        raise Exception(f"Failed to get video information: {str(e)}")

class DownloadError(Exception):
    """Custom exception for download errors"""
    pass

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass