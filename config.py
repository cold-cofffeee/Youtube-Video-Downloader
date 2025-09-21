# config.py
import os

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    
    # Download Configuration
    DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER') or 'downloads'
    MAX_CONCURRENT_DOWNLOADS = int(os.environ.get('MAX_CONCURRENT_DOWNLOADS') or 3)
    MAX_DOWNLOAD_SIZE = int(os.environ.get('MAX_DOWNLOAD_SIZE') or 2147483648)  # 2GB default
    
    # File Management
    HISTORY_FILE = 'download_history.json'
    AUTO_CLEANUP_DAYS = int(os.environ.get('AUTO_CLEANUP_DAYS') or 7)  # Auto-delete files after 7 days
    
    # Security
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE') or 10)
    
    # YouTube-dl Configuration
    YTDL_OPTS = {
        'format': 'best[height<=1080]',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': False,
        'extract_flat': False,
    }
    
    @staticmethod
    def init_app(app):
        # Create downloads directory
        if not os.path.exists(Config.DOWNLOAD_FOLDER):
            os.makedirs(Config.DOWNLOAD_FOLDER)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}