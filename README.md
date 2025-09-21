# ProTube - Professional YouTube Downloader

A modern, feature-rich YouTube video and playlist downloader with a beautiful web interface.

## 🚀 Features

### Core Features
- **Single Video Downloads** - Download individual YouTube videos in various qualities
- **Playlist Downloads** - Download entire playlists with progress tracking
- **Multiple Quality Options** - Choose from 1080p, 720p, 480p, 360p, or auto-select highest/lowest
- **Audio-Only Downloads** - Extract audio in MP3 format
- **Real-time Progress Tracking** - Live download progress with speed and ETA
- **Download Queue Management** - View and manage active downloads
- **Download History** - Keep track of all your downloads with metadata

### Advanced Features
- **Modern Responsive UI** - Beautiful, mobile-friendly interface
- **Real-time Notifications** - Toast notifications for all actions
- **URL Validation** - Smart YouTube URL detection and validation
- **File Management** - Organized downloads with proper naming
- **Error Handling** - Comprehensive error handling with user-friendly messages
- **Background Processing** - Non-blocking downloads using threading
- **Auto-cleanup** - Optional automatic cleanup of old files

### Technical Features
- **REST API** - Full API for programmatic access
- **Progress Callbacks** - Real-time download progress updates
- **Concurrent Downloads** - Support for multiple simultaneous downloads
- **File Size Tracking** - Monitor download sizes and total storage
- **Session Management** - Persistent download history
- **Rate Limiting** - Built-in protection against abuse

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Youtube-Video-Downloader
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://127.0.0.1:5000`

## 📋 Requirements

- Python 3.7+
- Flask 3.0.0
- pytube 15.0.0
- requests 2.31.0
- Werkzeug 3.0.1

## 🎯 Usage

### Web Interface

1. **Enter URL**: Paste a YouTube video or playlist URL
2. **Analyze**: Click "Analyze" to get video information
3. **Configure**: Select quality and format options
4. **Download**: Click "Start Download" to begin
5. **Monitor**: Track progress in real-time
6. **Manage**: View history and manage downloads

### API Endpoints

#### Get Video Information
```http
POST /get_video_info
Content-Type: application/json

{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

#### Start Download
```http
POST /download
Content-Type: application/json

{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "720p",
    "type": "video"
}
```

#### Check Download Status
```http
GET /download_status/{download_id}
```

#### Get Download History
```http
GET /history
```

#### List Active Downloads
```http
GET /downloads
```

## 🎨 Interface Overview

### Main Features
- **Download Tab**: Main download interface with URL input and options
- **History Tab**: View all completed downloads with metadata
- **Queue Tab**: Monitor active downloads with progress bars

### Quality Options
- **Highest Available**: Automatically selects best quality
- **1080p (Full HD)**: High definition download
- **720p (HD)**: Standard HD quality
- **480p**: Standard definition
- **360p**: Lower quality for faster downloads
- **Lowest Available**: Minimum quality for bandwidth saving

### Format Options
- **Video (MP4)**: Full video with audio
- **Audio Only (MP3)**: Extract audio track only

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for sessions
- `DOWNLOAD_FOLDER`: Directory for downloaded files (default: 'downloads')
- `MAX_CONCURRENT_DOWNLOADS`: Maximum simultaneous downloads (default: 3)
- `MAX_DOWNLOAD_SIZE`: Maximum file size in bytes (default: 2GB)
- `AUTO_CLEANUP_DAYS`: Days before auto-cleanup (default: 7)
- `RATE_LIMIT_PER_MINUTE`: API rate limit (default: 10)

### File Structure
```
Youtube-Video-Downloader/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── utils.py              # Utility functions
├── requirements.txt      # Python dependencies
├── download_history.json # Download history storage
├── downloads/           # Downloaded files directory
├── static/
│   ├── style.css        # Modern CSS styles
│   └── script.js        # Frontend JavaScript
└── templates/
    ├── home.html        # Main interface
    └── success.html     # Success page
```

## 🚀 Features in Detail

### Smart URL Detection
- Supports various YouTube URL formats
- Automatically detects video vs playlist URLs
- Validates URLs before processing

### Progress Tracking
- Real-time download progress
- File size and speed information
- ETA calculations
- Playlist progress tracking

### Error Handling
- Network error recovery
- Invalid URL detection
- File system error handling
- User-friendly error messages

### File Management
- Automatic filename sanitization
- Duplicate handling
- File size tracking
- Optional auto-cleanup

## 🔒 Security Features

- Input validation and sanitization
- Rate limiting protection
- File path security
- CSRF protection
- Safe filename handling

## 🎯 Future Enhancements

- [ ] Video format conversion
- [ ] Subtitle downloads
- [ ] Batch URL processing
- [ ] Download scheduling
- [ ] Cloud storage integration
- [ ] Mobile app
- [ ] User authentication
- [ ] Download statistics

## 🐛 Troubleshooting

### Common Issues

1. **Downloads failing**: Check internet connection and YouTube URL validity
2. **Slow downloads**: Try lower quality settings or check bandwidth
3. **File not found**: Ensure download completed successfully
4. **Permission errors**: Check write permissions for downloads folder

### Error Messages
- "Invalid YouTube URL": The URL format is not recognized
- "Video not available": The video may be private or deleted
- "Quality not available": Try a different quality setting
- "Download failed": Network or server error occurred

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## ⚠️ Disclaimer

This tool is for educational purposes only. Please respect YouTube's Terms of Service and copyright laws. Only download content you have permission to download.

## 🙏 Acknowledgments

- [pytube](https://github.com/pytube/pytube) for YouTube downloading capabilities
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Font Awesome](https://fontawesome.com/) for icons
- [Google Fonts](https://fonts.google.com/) for typography

---

**ProTube** - Making YouTube downloads simple, fast, and beautiful! 🎥✨

- **Easy to Use**: Just paste the YouTube video URL, and the app will download the highest resolution video for you.
- **Fast Download**: Utilizes Pytube to efficiently download videos.
- **Minimalistic Design**: Clean and straightforward interface.

## How to Use

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/your-repository.git
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the Flask app:

    ```bash
    python app.py
    ```

4. Open your browser and go to [http://localhost:5000](http://localhost:5000)

5. Paste a YouTube video URL, click download, and enjoy!

## Technologies Used

- Flask
- Pytube

## Contributing

Feel free to contribute to the project by opening issues or submitting pull requests. Your feedback and suggestions are highly appreciated.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Make sure to replace "your-username" and "your-repository" with your actual GitHub username and repository name. Also, ensure that you have a `requirements.txt` file containing the necessary dependencies.
