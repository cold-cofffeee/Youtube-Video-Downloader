# app.py
from flask import Flask, render_template, request, jsonify, send_file, session
import os
import re
import threading
import time
import uuid
from datetime import datetime
import json
import subprocess
import sys

# Try multiple YouTube libraries for better compatibility
try:
    from pytubefix import YouTube, Playlist
    YOUTUBE_LIB = 'pytubefix'
    print("Using pytubefix library")
except ImportError:
    try:
        from pytube import YouTube, Playlist
        YOUTUBE_LIB = 'pytube'
        print("Using pytube library")
    except ImportError:
        YOUTUBE_LIB = 'yt-dlp'
        print("Using yt-dlp as fallback")

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Configuration
DOWNLOAD_FOLDER = 'downloads'
HISTORY_FILE = 'download_history.json'
MAX_CONCURRENT_DOWNLOADS = 3

# Create downloads directory if it doesn't exist
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Global variables for tracking downloads
active_downloads = {}
download_queue = []
download_history = []

def load_history():
    """Load download history from file"""
    global download_history
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                download_history = json.load(f)
    except:
        download_history = []

def save_history():
    """Save download history to file"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(download_history, f, indent=2)
    except:
        pass

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def get_video_info_safe(url):
    """Get video info using multiple methods with fallbacks"""
    try:
        if YOUTUBE_LIB == 'pytubefix':
            from pytubefix import YouTube, Playlist
            if 'playlist' in url.lower() or 'list=' in url:
                playlist = Playlist(url)
                return {
                    'success': True,
                    'type': 'playlist',
                    'title': playlist.title or 'Untitled Playlist',
                    'thumbnail': '',
                    'duration': 0,
                    'description': f"Playlist with {len(list(playlist.video_urls))} videos"
                }
            else:
                yt = YouTube(url)
                return {
                    'success': True,
                    'type': 'video',
                    'title': yt.title or 'Untitled Video',
                    'thumbnail': yt.thumbnail_url or '',
                    'duration': yt.length or 0,
                    'description': (yt.description[:200] + '...') if yt.description and len(yt.description) > 200 else (yt.description or 'No description available')
                }
        
        elif YOUTUBE_LIB == 'pytube':
            from pytube import YouTube, Playlist
            if 'playlist' in url.lower() or 'list=' in url:
                playlist = Playlist(url)
                return {
                    'success': True,
                    'type': 'playlist',
                    'title': playlist.title or 'Untitled Playlist',
                    'thumbnail': '',
                    'duration': 0,
                    'description': f"Playlist with {len(list(playlist.video_urls))} videos"
                }
            else:
                yt = YouTube(url)
                return {
                    'success': True,
                    'type': 'video',
                    'title': yt.title or 'Untitled Video',
                    'thumbnail': yt.thumbnail_url or '',
                    'duration': yt.length or 0,
                    'description': (yt.description[:200] + '...') if yt.description and len(yt.description) > 200 else (yt.description or 'No description available')
                }
        
        else:  # yt-dlp fallback
            return get_video_info_ytdlp(url)
            
    except Exception as e:
        print(f"Error with {YOUTUBE_LIB}: {str(e)}")
        # Try yt-dlp as fallback
        try:
            return get_video_info_ytdlp(url)
        except Exception as e2:
            print(f"Error with yt-dlp fallback: {str(e2)}")
            return {
                'success': False,
                'error': f"Failed to get video info: {str(e)}"
            }

def get_video_info_ytdlp(url):
    """Get video info using yt-dlp with enhanced options"""
    try:
        import subprocess
        import json
        
        cmd = [
            'yt-dlp', 
            '--dump-json', 
            '--no-download',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            '--extractor-args', 'youtube:player_client=web,android',
            '--no-warnings',
            '--no-check-certificate',
            '--prefer-free-formats',
            '--add-header', 'Accept-Language:en-US,en;q=0.9',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        
        if result.returncode == 0:
            # Parse the first line of JSON output
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    try:
                        info = json.loads(line)
                        return {
                            'success': True,
                            'type': 'playlist' if info.get('_type') == 'playlist' else 'video',
                            'title': info.get('title', 'Untitled Video'),
                            'thumbnail': info.get('thumbnail', ''),
                            'duration': info.get('duration', 0),
                            'description': (info.get('description', '')[:200] + '...') if info.get('description', '') and len(info.get('description', '')) > 200 else (info.get('description', '') or 'No description available')
                        }
                    except json.JSONDecodeError:
                        continue
            
            # If we get here, no valid JSON was found
            return {
                'success': False,
                'error': "Could not parse video information"
            }
        else:
            error_msg = result.stderr or "Unknown error"
            return {
                'success': False,
                'error': f"yt-dlp info error: {error_msg}"
            }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': "Timeout while getting video information"
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"yt-dlp info failed: {str(e)}"
        }

def download_video_safe(url, quality='highest', download_type='video', download_id=None):
    """Download video using multiple methods with fallbacks"""
    try:
        if YOUTUBE_LIB == 'pytubefix':
            return download_with_pytubefix(url, quality, download_type, download_id)
        elif YOUTUBE_LIB == 'pytube':
            return download_with_pytube(url, quality, download_type, download_id)
        else:
            return download_with_ytdlp(url, quality, download_type, download_id)
    except Exception as e:
        print(f"Error with {YOUTUBE_LIB}: {str(e)}")
        # Try yt-dlp as fallback
        try:
            return download_with_ytdlp(url, quality, download_type, download_id)
        except Exception as e2:
            print(f"Error with yt-dlp fallback: {str(e2)}")
            if download_id and download_id in active_downloads:
                active_downloads[download_id]['status'] = 'error'
                active_downloads[download_id]['error'] = str(e)
            return False

def download_with_pytubefix(url, quality, download_type, download_id):
    """Download using pytubefix with enhanced settings"""
    try:
        from pytubefix import YouTube
        
        def progress_callback(stream, chunk, bytes_remaining):
            if download_id and download_id in active_downloads:
                total_size = stream.filesize
                downloaded = total_size - bytes_remaining
                progress = (downloaded / total_size) * 100
                active_downloads[download_id]['progress'] = progress
        
        # Initialize with enhanced settings
        yt = YouTube(
            url, 
            on_progress_callback=progress_callback,
            use_oauth=False,
            allow_oauth_cache=False
        )
        
        if download_type == 'audio':
            # Try different audio stream options
            stream = (yt.streams.filter(only_audio=True, file_extension='mp4').first() or
                     yt.streams.filter(only_audio=True).first())
            filename = f"{sanitize_filename(yt.title)}.mp3"
        else:
            # Priority: Get video WITH audio - progressive streams are guaranteed to have both
            if quality == 'highest':
                # First try progressive (video+audio), then fallback with explicit audio check
                stream = (yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first() or
                         yt.streams.filter(file_extension='mp4', adaptive=False).order_by('resolution').desc().first() or
                         yt.streams.filter(file_extension='mp4').order_by('resolution').desc().first())
            elif quality == 'lowest':
                # Try progressive first for lowest quality with audio
                stream = (yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').asc().first() or
                         yt.streams.filter(file_extension='mp4', adaptive=False).order_by('resolution').asc().first() or
                         yt.streams.filter(file_extension='mp4').order_by('resolution').asc().first())
            else:
                # Try exact quality with progressive streams first (guaranteed video+audio)
                stream = (yt.streams.filter(progressive=True, file_extension='mp4', res=quality).first() or
                         yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first() or
                         yt.streams.filter(file_extension='mp4', res=quality, adaptive=False).first() or
                         yt.streams.filter(file_extension='mp4', adaptive=False).order_by('resolution').desc().first())
            
            # Final fallback - ensure we get SOMETHING with audio
            if not stream:
                print("Warning: No progressive stream found, trying any available stream")
                stream = yt.streams.filter(file_extension='mp4').first() or yt.streams.first()
            
            filename = f"{sanitize_filename(yt.title)}.mp4"
        
        if stream:
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            
            # Download with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    stream.download(filename=filepath)
                    break
                except Exception as e:
                    print(f"Download attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(2)  # Wait before retry
            
            if download_id and download_id in active_downloads:
                active_downloads[download_id]['status'] = 'completed'
                active_downloads[download_id]['progress'] = 100
                active_downloads[download_id]['filepath'] = filepath
            
            return filename
        else:
            raise Exception("No suitable stream found")
            
    except Exception as e:
        print(f"Pytubefix download error: {str(e)}")
        if download_id and download_id in active_downloads:
            active_downloads[download_id]['status'] = 'error'
            active_downloads[download_id]['error'] = f"Pytubefix error: {str(e)}"
        return False

def download_with_pytube(url, quality, download_type, download_id):
    """Download using original pytube"""
    from pytube import YouTube
    
    def progress_callback(stream, chunk, bytes_remaining):
        if download_id and download_id in active_downloads:
            total_size = stream.filesize
            downloaded = total_size - bytes_remaining
            progress = (downloaded / total_size) * 100
            active_downloads[download_id]['progress'] = progress
    
    yt = YouTube(url, on_progress_callback=progress_callback)
    
    if download_type == 'audio':
        stream = yt.streams.filter(only_audio=True).first()
        filename = f"{sanitize_filename(yt.title)}.mp3"
    else:
        # Prioritize progressive streams (video + audio) for complete downloads
        if quality == 'highest':
            stream = (yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first() or
                     yt.streams.filter(file_extension='mp4').order_by('resolution').desc().first() or
                     yt.streams.get_highest_resolution())
        elif quality == 'lowest':
            stream = (yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').asc().first() or
                     yt.streams.filter(file_extension='mp4').order_by('resolution').asc().first() or
                     yt.streams.get_lowest_resolution())
        else:
            # Try exact quality with progressive (video+audio) first
            stream = (yt.streams.filter(progressive=True, file_extension='mp4', res=quality).first() or
                     yt.streams.filter(file_extension='mp4', res=quality).first() or
                     yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first() or
                     yt.streams.filter(file_extension='mp4').order_by('resolution').desc().first() or
                     yt.streams.get_highest_resolution())
        
        filename = f"{sanitize_filename(yt.title)}.mp4"
    
    if stream:
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        stream.download(filename=filepath)
        
        if download_id and download_id in active_downloads:
            active_downloads[download_id]['status'] = 'completed'
            active_downloads[download_id]['progress'] = 100
            active_downloads[download_id]['filepath'] = filepath
        
        return filename
    return False

def download_with_ytdlp(url, quality, download_type, download_id):
    """Download using yt-dlp with enhanced options to bypass restrictions"""
    try:
        import subprocess
        
        # Get video title first for filename
        info_cmd = [
            'yt-dlp', 
            '--dump-json', 
            '--no-download',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            '--extractor-args', 'youtube:player_client=web',
            url
        ]
        
        try:
            info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
            if info_result.returncode == 0:
                import json
                info = json.loads(info_result.stdout.split('\n')[0])
                video_title = sanitize_filename(info.get('title', 'Unknown'))
            else:
                video_title = 'Unknown'
        except:
            video_title = 'Unknown'
        
        if download_type == 'audio':
            filename = f"{video_title}.%(ext)s"
            cmd = [
                'yt-dlp', 
                '-x', 
                '--audio-format', 'mp3',
                '--audio-quality', '0',  # best audio quality
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                '--extractor-args', 'youtube:player_client=web,android',
                '--no-warnings',
                '--no-check-certificate',
                '--prefer-free-formats',
                '--add-header', 'Accept-Language:en-US,en;q=0.9',
                '--sleep-interval', '1',
                '--max-sleep-interval', '5',
                '-o', os.path.join(DOWNLOAD_FOLDER, filename),
                url
            ]
        else:
            filename = f"{video_title}.%(ext)s"
            
            # Set quality format - FORCE video+audio combination
            if quality == 'highest':
                format_selector = 'best[ext=mp4][acodec!=none][vcodec!=none]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif quality == 'lowest':
                format_selector = 'worst[ext=mp4][acodec!=none][vcodec!=none]/worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst'
            else:
                # Extract resolution number (e.g., "720p" -> "720")
                res = quality.replace('p', '') if 'p' in quality else '720'
                format_selector = f'best[height<={res}][ext=mp4][acodec!=none][vcodec!=none]/bestvideo[height<={res}][ext=mp4]+bestaudio[ext=m4a]/best[height<={res}][ext=mp4]/best[height<={res}]/best'
            
            cmd = [
                'yt-dlp',
                '-f', format_selector,
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                '--extractor-args', 'youtube:player_client=web,android',
                '--no-warnings',
                '--no-check-certificate',
                '--prefer-free-formats',
                '--add-header', 'Accept-Language:en-US,en;q=0.9',
                '--sleep-interval', '1',
                '--max-sleep-interval', '5',
                '--embed-thumbnail',
                '--add-metadata',
                '-o', os.path.join(DOWNLOAD_FOLDER, filename),
                url
            ]
        
        # Update progress simulation (since yt-dlp progress is hard to parse in real-time)
        def update_progress():
            progress_steps = [10, 25, 40, 55, 70, 85, 95]
            for step in progress_steps:
                if download_id and download_id in active_downloads:
                    if active_downloads[download_id]['status'] == 'downloading':
                        active_downloads[download_id]['progress'] = step
                        time.sleep(2)
                    else:
                        break
        
        # Start progress simulation
        if download_id and download_id in active_downloads:
            active_downloads[download_id]['status'] = 'downloading'
            progress_thread = threading.Thread(target=update_progress)
            progress_thread.daemon = True
            progress_thread.start()
        
        # Execute download
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 minute timeout
        
        if result.returncode == 0:
            # Find the downloaded file
            import glob
            pattern = os.path.join(DOWNLOAD_FOLDER, f"{video_title}.*")
            files = glob.glob(pattern)
            
            if not files:
                # Fallback: look for any recent files
                pattern = os.path.join(DOWNLOAD_FOLDER, "*")
                files = glob.glob(pattern)
                if files:
                    # Get the most recently created file
                    latest_file = max(files, key=os.path.getctime)
                    filename = os.path.basename(latest_file)
                else:
                    filename = f"{video_title}.{'mp3' if download_type == 'audio' else 'mp4'}"
            else:
                latest_file = max(files, key=os.path.getctime)
                filename = os.path.basename(latest_file)
            
            if download_id and download_id in active_downloads:
                active_downloads[download_id]['status'] = 'completed'
                active_downloads[download_id]['progress'] = 100
                active_downloads[download_id]['filepath'] = latest_file if 'latest_file' in locals() else os.path.join(DOWNLOAD_FOLDER, filename)
            
            return filename
        else:
            error_msg = result.stderr or "Download failed"
            print(f"yt-dlp error: {error_msg}")
            if download_id and download_id in active_downloads:
                active_downloads[download_id]['status'] = 'error'
                active_downloads[download_id]['error'] = f"yt-dlp error: {error_msg}"
            return False
            
    except subprocess.TimeoutExpired:
        error_msg = "Download timeout - video may be too large or connection too slow"
        print(error_msg)
        if download_id and download_id in active_downloads:
            active_downloads[download_id]['status'] = 'error'
            active_downloads[download_id]['error'] = error_msg
        return False
    except Exception as e:
        error_msg = f"Download exception: {str(e)}"
        print(error_msg)
        if download_id and download_id in active_downloads:
            active_downloads[download_id]['status'] = 'error'
            active_downloads[download_id]['error'] = error_msg
        return False

def format_bytes(bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def progress_callback(stream, chunk, bytes_remaining):
    """Progress callback for downloads"""
    download_id = getattr(stream, 'download_id', None)
    if download_id and download_id in active_downloads:
        total_size = stream.filesize
        downloaded = total_size - bytes_remaining
        progress = (downloaded / total_size) * 100 if total_size > 0 else 0
        
        active_downloads[download_id].update({
            'progress': round(progress, 1),
            'downloaded': format_bytes(downloaded),
            'total_size': format_bytes(total_size),
            'status': 'downloading'
        })

def download_video(url, quality, download_type, download_id):
    """Download a single video"""
    try:
        active_downloads[download_id]['status'] = 'processing'
        
        yt = YouTube(url)
        yt.register_on_progress_callback(progress_callback)
        
        # Set download_id on the stream for progress tracking
        if download_type == 'audio':
            stream = yt.streams.filter(only_audio=True).first()
        elif quality == 'highest':
            stream = yt.streams.get_highest_resolution()
        elif quality == 'lowest':
            stream = yt.streams.get_lowest_resolution()
        else:
            stream = yt.streams.filter(res=quality).first()
            if not stream:
                stream = yt.streams.get_highest_resolution()
        
        if not stream:
            raise Exception("No suitable stream found")
            
        stream.download_id = download_id
        
        # Create filename
        safe_title = sanitize_filename(yt.title)
        if download_type == 'audio':
            filename = f"{safe_title}.mp4"  # pytube downloads audio as mp4
        else:
            filename = f"{safe_title}_{quality}.{stream.subtype}"
            
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # Update download info
        active_downloads[download_id].update({
            'title': yt.title,
            'thumbnail': yt.thumbnail_url,
            'duration': yt.length,
            'filename': filename,
            'filepath': filepath
        })
        
        # Download the file
        stream.download(output_path=DOWNLOAD_FOLDER, filename=filename)
        
        # Mark as completed
        active_downloads[download_id]['status'] = 'completed'
        active_downloads[download_id]['progress'] = 100
        active_downloads[download_id]['completed_at'] = datetime.now().isoformat()
        
        # Add to history
        history_entry = {
            'id': download_id,
            'title': yt.title,
            'url': url,
            'quality': quality,
            'type': download_type,
            'filename': filename,
            'downloaded_at': datetime.now().isoformat(),
            'file_size': format_bytes(os.path.getsize(filepath)) if os.path.exists(filepath) else 'Unknown'
        }
        download_history.append(history_entry)
        save_history()
        
    except Exception as e:
        active_downloads[download_id]['status'] = 'error'
        active_downloads[download_id]['error'] = str(e)

def download_playlist(url, quality, download_type, download_id):
    """Download all videos from a playlist"""
    try:
        active_downloads[download_id]['status'] = 'processing'
        
        # Import the appropriate library
        if YOUTUBE_LIB == 'pytubefix':
            from pytubefix import Playlist
        else:
            from pytube import Playlist
            
        playlist = Playlist(url)
        video_urls = list(playlist.video_urls)
        
        active_downloads[download_id].update({
            'total_videos': len(video_urls),
            'completed_videos': 0,
            'playlist_title': playlist.title,
            'downloaded_files': []
        })
        
        successful_downloads = 0
        
        for i, video_url in enumerate(video_urls):
            try:
                print(f"Downloading video {i+1}/{len(video_urls)}: {video_url}")
                
                # Create individual download for each video
                video_download_id = f"{download_id}_video_{i}"
                active_downloads[video_download_id] = {
                    'url': video_url,
                    'quality': quality,
                    'type': download_type,
                    'status': 'queued',
                    'progress': 0,
                    'parent_playlist': download_id
                }
                
                result = download_video_safe(video_url, quality, download_type, video_download_id)
                
                if result:
                    successful_downloads += 1
                    active_downloads[download_id]['downloaded_files'].append(result)
                    print(f"Successfully downloaded: {result}")
                
                active_downloads[download_id]['completed_videos'] += 1
                active_downloads[download_id]['progress'] = (active_downloads[download_id]['completed_videos'] / len(video_urls)) * 100
                
            except Exception as e:
                print(f"Error downloading video {i+1}: {e}")
                continue
        
        active_downloads[download_id]['status'] = 'completed'
        active_downloads[download_id]['progress'] = 100
        
        # Return summary of downloads
        return f"Playlist: {successful_downloads}/{len(video_urls)} videos downloaded"
        
    except Exception as e:
        print(f"Playlist download error: {str(e)}")
        active_downloads[download_id]['status'] = 'error'
        active_downloads[download_id]['error'] = str(e)
        return False

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/get_video_info', methods=['POST'])
def get_video_info():
    """Get video information without downloading"""
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate YouTube URL
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=[\w-]+',
            r'(?:https?://)?youtu\.be/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/.*'
        ]
        
        if not any(re.match(pattern, url) for pattern in youtube_patterns):
            return jsonify({'error': 'Please provide a valid YouTube URL'}), 400
        
        info = get_video_info_safe(url)
        
        if info['success']:
            return jsonify(info), 200
        else:
            return jsonify({'error': info.get('error', 'Failed to get video information')}), 400
            
    except Exception as e:
        print(f"Error in get_video_info: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/download', methods=['POST'])
def download():
    """Start download process"""
    try:
        data = request.json
        url = data.get('url')
        quality = data.get('quality', 'highest')
        download_type = data.get('type', 'video')  # 'video' or 'audio'
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate YouTube URL
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=[\w-]+',
            r'(?:https?://)?youtu\.be/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/.*'
        ]
        
        if not any(re.match(pattern, url) for pattern in youtube_patterns):
            return jsonify({'error': 'Please provide a valid YouTube URL'}), 400
        
        # Generate unique download ID
        download_id = str(uuid.uuid4())
        
        # Get video info first to check if it's a playlist
        info = get_video_info_safe(url)
        if not info['success']:
            return jsonify({'error': 'Failed to analyze video/playlist'}), 400

        filename = f"{sanitize_filename(info['title'])}.{'mp3' if download_type == 'audio' else 'mp4'}"
        
        # Initialize download tracking
        active_downloads[download_id] = {
            'url': url,
            'filename': filename,
            'quality': quality,
            'type': download_type,
            'status': 'starting',
            'progress': 0,
            'started_at': datetime.now(),
            'error': None,
            'filepath': None,
            'is_playlist': info.get('type') == 'playlist'
        }
        
        # Start download in background thread
        def download_worker():
            try:
                active_downloads[download_id]['status'] = 'downloading'
                
                # Check if it's a playlist
                if info.get('type') == 'playlist':
                    result = download_playlist(url, quality, download_type, download_id)
                else:
                    result = download_video_safe(url, quality, download_type, download_id)
                
                if result:
                    # Add to history
                    history_item = {
                        'id': download_id,
                        'url': url,
                        'filename': result if not info.get('type') == 'playlist' else f"Playlist: {info['title']}",
                        'quality': quality,
                        'type': download_type,
                        'downloaded_at': datetime.now().isoformat(),
                        'status': 'completed',
                        'is_playlist': info.get('type') == 'playlist'
                    }
                    download_history.append(history_item)
                    save_history()
                    print(f"Download completed: {result}")
                else:
                    if download_id in active_downloads:
                        active_downloads[download_id]['status'] = 'error'
                        if 'error' not in active_downloads[download_id]:
                            active_downloads[download_id]['error'] = 'Download failed'
                    print(f"Download failed for: {url}")
                    
            except Exception as e:
                print(f"Download error: {str(e)}")
                if download_id in active_downloads:
                    active_downloads[download_id]['status'] = 'error'
                    active_downloads[download_id]['error'] = str(e)
        
        download_thread = threading.Thread(target=download_worker)
        download_thread.daemon = True
        download_thread.start()
        
        return jsonify({
            'download_id': download_id,
            'filename': filename,
            'status': 'started'
        })
        
    except Exception as e:
        print(f"Error in download route: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/download_status/<download_id>')
def download_status(download_id):
    """Get download status"""
    if download_id in active_downloads:
        return jsonify(active_downloads[download_id])
    else:
        return jsonify({'error': 'Download not found'}), 404

@app.route('/downloads')
def list_downloads():
    """List all downloaded files"""
    try:
        files = []
        if os.path.exists(DOWNLOAD_FOLDER):
            for filename in os.listdir(DOWNLOAD_FOLDER):
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'download_url': f'/download_file/{filename}'
                    })
        
        return jsonify({
            'files': files,
            'download_folder': os.path.abspath(DOWNLOAD_FOLDER),
            'total_files': len(files)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_file/<identifier>')
def download_file(identifier):
    """Download a specific file by filename or download_id"""
    try:
        # First try as download_id
        if identifier in active_downloads and active_downloads[identifier]['status'] == 'completed':
            filepath = active_downloads[identifier].get('filepath')
            if filepath and os.path.exists(filepath):
                return send_file(filepath, as_attachment=True)
        
        # Then try as direct filename
        filepath = os.path.join(DOWNLOAD_FOLDER, identifier)
        if os.path.exists(filepath):
            return send_file(
                filepath,
                as_attachment=True,
                download_name=identifier
            )
        
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404

@app.route('/downloads/')
def downloads_folder():
    """Show downloads folder contents in browser"""
    try:
        files = []
        download_path = os.path.abspath(DOWNLOAD_FOLDER)
        
        if os.path.exists(DOWNLOAD_FOLDER):
            for filename in os.listdir(DOWNLOAD_FOLDER):
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    size_mb = round(stat.st_size / (1024 * 1024), 2)
                    files.append({
                        'filename': filename,
                        'size_mb': size_mb,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'download_url': f'/download_file/{filename}'
                    })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Downloaded Files</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; margin-bottom: 10px; }}
                .info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; font-weight: 600; }}
                .download-btn {{ background: #007bff; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-size: 12px; }}
                .download-btn:hover {{ background: #0056b3; }}
                .empty {{ text-align: center; color: #666; font-style: italic; padding: 40px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📁 Downloaded Files</h1>
                <div class="info">
                    <strong>Download Location:</strong> {download_path}<br>
                    <strong>Total Files:</strong> {len(files)}
                </div>
                
                {'<div class="empty">No files downloaded yet. Start downloading videos to see them here!</div>' if not files else f'''
                <table>
                    <thead>
                        <tr>
                            <th>Filename</th>
                            <th>Size (MB)</th>
                            <th>Downloaded</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join([f'''
                        <tr>
                            <td>{file["filename"]}</td>
                            <td>{file["size_mb"]}</td>
                            <td>{file["modified"]}</td>
                            <td><a href="{file["download_url"]}" class="download-btn">📥 Download</a></td>
                        </tr>
                        ''' for file in files])}
                    </tbody>
                </table>
                '''}
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/history')
def history():
    """Get download history"""
    return jsonify(download_history)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear download history"""
    global download_history
    download_history = []
    save_history()
    return jsonify({'message': 'History cleared'})

@app.route('/open_downloads_folder')
def open_downloads_folder():
    """Open downloads folder in file explorer"""
    try:
        import platform
        import subprocess
        import os
        
        downloads_path = os.path.abspath(DOWNLOAD_FOLDER)
        print(f"Attempting to open folder: {downloads_path}")
        
        if platform.system() == 'Windows':
            # Use start command for Windows
            result = subprocess.run(['cmd', '/c', 'start', '', downloads_path], capture_output=True, text=True)
            print(f"Windows command result: {result.returncode}, {result.stdout}, {result.stderr}")
        elif platform.system() == 'Darwin':  # macOS
            result = subprocess.run(['open', downloads_path], capture_output=True, text=True)
            print(f"macOS command result: {result.returncode}, {result.stdout}, {result.stderr}")
        else:  # Linux
            result = subprocess.run(['xdg-open', downloads_path], capture_output=True, text=True)
            print(f"Linux command result: {result.returncode}, {result.stdout}, {result.stderr}")
            
        return jsonify({'success': True, 'message': 'Folder opened', 'path': downloads_path})
    except Exception as e:
        print(f"Error opening folder: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete_download/<download_id>', methods=['DELETE'])
def delete_download(download_id):
    """Delete a download and its file"""
    if download_id in active_downloads:
        filepath = active_downloads[download_id].get('filepath')
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        
        del active_downloads[download_id]
        return jsonify({'message': 'Download deleted'})
    
    return jsonify({'error': 'Download not found'}), 404

if __name__ == '__main__':
    load_history()
    app.run(debug=True, use_reloader=False)
