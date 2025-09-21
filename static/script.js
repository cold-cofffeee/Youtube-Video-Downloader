// script.js
class YouTubeDownloader {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.currentDownloadId = null;
        this.progressCheckInterval = null;
        this.loadHistory();
        this.loadQueue();
    }

    initializeElements() {
        this.elements = {
            urlInput: document.getElementById('urlInput'),
            analyzeBtn: document.getElementById('analyzeBtn'),
            downloadBtn: document.getElementById('downloadBtn'),
            videoInfo: document.getElementById('videoInfo'),
            videoThumbnail: document.getElementById('videoThumbnail'),
            videoTitle: document.getElementById('videoTitle'),
            videoDescription: document.getElementById('videoDescription'),
            videoDuration: document.getElementById('videoDuration'),
            videoType: document.getElementById('videoType'),
            qualitySelect: document.getElementById('qualitySelect'),
            formatSelect: document.getElementById('formatSelect'),
            progressModal: document.getElementById('progressModal'),
            currentDownload: document.getElementById('currentDownload'),
            closeModal: document.getElementById('closeModal'),
            historyList: document.getElementById('historyList'),
            queueList: document.getElementById('queueList'),
            clearHistoryBtn: document.getElementById('clearHistoryBtn'),
            toastContainer: document.getElementById('toastContainer'),
            navBtns: document.querySelectorAll('.nav-btn'),
            tabContents: document.querySelectorAll('.tab-content')
        };
    }

    bindEvents() {
        this.elements.analyzeBtn.addEventListener('click', () => this.analyzeVideo());
        this.elements.downloadBtn.addEventListener('click', () => this.startDownload());
        this.elements.closeModal.addEventListener('click', () => this.closeProgressModal());
        this.elements.clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        
        // Tab navigation
        this.elements.navBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Enter key support for URL input
        this.elements.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.analyzeVideo();
            }
        });
    }

    switchTab(tabName) {
        // Update nav buttons
        this.elements.navBtns.forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        this.elements.tabContents.forEach(content => content.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Load content based on tab
        if (tabName === 'history') {
            this.loadHistory();
        } else if (tabName === 'queue') {
            this.loadQueue();
        }
    }

    async analyzeVideo() {
        const url = this.elements.urlInput.value.trim();
        if (!url) {
            this.showToast('Please enter a YouTube URL', 'error');
            return;
        }

        if (!this.isValidYouTubeUrl(url)) {
            this.showToast('Please enter a valid YouTube URL', 'error');
            return;
        }

        this.setLoading(this.elements.analyzeBtn, true);

        try {
            const response = await fetch('/get_video_info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url })
            });

            const data = await response.json();

            if (response.ok) {
                this.displayVideoInfo(data);
            } else {
                this.showToast(data.error || 'Failed to analyze video', 'error');
            }
        } catch (error) {
            this.showToast('Network error. Please try again.', 'error');
        } finally {
            this.setLoading(this.elements.analyzeBtn, false);
        }
    }

    displayVideoInfo(data) {
        if (data.type === 'playlist') {
            this.elements.videoThumbnail.style.display = 'none';
            this.elements.videoTitle.textContent = data.title;
            this.elements.videoDescription.textContent = data.description;
            this.elements.videoDuration.textContent = '';
            this.elements.videoType.textContent = `Playlist (${data.video_count} videos)`;
            
            // Hide quality options for playlists - will use default highest
            this.elements.qualitySelect.disabled = false;
        } else {
            this.elements.videoThumbnail.src = data.thumbnail;
            this.elements.videoThumbnail.style.display = 'block';
            this.elements.videoTitle.textContent = data.title;
            this.elements.videoDescription.textContent = data.description;
            this.elements.videoDuration.textContent = this.formatDuration(data.duration);
            this.elements.videoType.textContent = 'Single Video';

            // Update quality options
            this.updateQualityOptions(data.available_qualities);
        }

        this.elements.videoInfo.style.display = 'block';
    }

    updateQualityOptions(availableQualities) {
        const qualitySelect = this.elements.qualitySelect;
        
        // Clear existing options except for default ones
        const defaultOptions = ['highest', 'lowest'];
        Array.from(qualitySelect.options).forEach(option => {
            if (!defaultOptions.includes(option.value) && option.value !== 'highest' && option.value !== 'lowest') {
                option.remove();
            }
        });

        // Add available qualities
        if (availableQualities && availableQualities.length > 0) {
            availableQualities.sort((a, b) => {
                const aNum = parseInt(a);
                const bNum = parseInt(b);
                return bNum - aNum; // Sort descending
            });

            availableQualities.forEach(quality => {
                if (quality) {
                    const option = document.createElement('option');
                    option.value = quality;
                    option.textContent = quality;
                    qualitySelect.insertBefore(option, qualitySelect.children[2]); // Insert after "highest"
                }
            });
        }
    }

    async startDownload() {
        const url = this.elements.urlInput.value.trim();
        const quality = this.elements.qualitySelect.value;
        const format = this.elements.formatSelect.value;

        if (!url) {
            this.showToast('Please enter a YouTube URL', 'error');
            return;
        }

        this.setLoading(this.elements.downloadBtn, true);

        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    quality: quality,
                    type: format
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentDownloadId = data.download_id;
                this.showProgressModal();
                this.startProgressTracking();
                this.showToast('Download started successfully!', 'success');
            } else {
                this.showToast(data.error || 'Failed to start download', 'error');
            }
        } catch (error) {
            this.showToast('Network error. Please try again.', 'error');
        } finally {
            this.setLoading(this.elements.downloadBtn, false);
        }
    }

    showProgressModal() {
        this.elements.progressModal.classList.add('active');
    }

    closeProgressModal() {
        this.elements.progressModal.classList.remove('active');
        if (this.progressCheckInterval) {
            clearInterval(this.progressCheckInterval);
        }
    }

    startProgressTracking() {
        if (this.progressCheckInterval) {
            clearInterval(this.progressCheckInterval);
        }

        this.progressCheckInterval = setInterval(async () => {
            if (!this.currentDownloadId) return;

            try {
                const response = await fetch(`/download_status/${this.currentDownloadId}`);
                const data = await response.json();

                if (response.ok) {
                    this.updateProgressDisplay(data);

                    if (data.status === 'completed' || data.status === 'error') {
                        clearInterval(this.progressCheckInterval);
                        
                        if (data.status === 'completed') {
                            this.showToast('Download completed successfully!', 'success');
                            setTimeout(() => this.closeProgressModal(), 2000);
                        } else {
                            this.showToast(data.error || 'Download failed', 'error');
                        }
                        
                        this.loadHistory();
                        this.loadQueue();
                    }
                }
            } catch (error) {
                console.error('Error checking download status:', error);
            }
        }, 1000);
    }

    updateProgressDisplay(data) {
        const container = this.elements.currentDownload;
        
        let html = `
            <div class="download-item">
                <h4>${data.title || 'Processing...'}</h4>
                <div class="download-meta">
                    <small>Status: ${this.capitalizeFirst(data.status)}</small>
                    <span class="status-badge status-${data.status}">${data.status}</span>
                </div>
        `;

        if (data.progress !== undefined) {
            html += `
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${data.progress}%"></div>
                </div>
                <div class="progress-text">
                    ${data.progress}% ${data.downloaded ? `(${data.downloaded}/${data.total_size})` : ''}
                </div>
            `;
        }

        if (data.playlist_title) {
            html += `<p><strong>Playlist:</strong> ${data.playlist_title}</p>`;
            if (data.total_videos) {
                html += `<p><strong>Progress:</strong> ${data.completed_videos || 0}/${data.total_videos} videos</p>`;
            }
        }

        if (data.error) {
            html += `<p class="error-message" style="color: var(--danger-color);">${data.error}</p>`;
        }

        html += '</div>';
        container.innerHTML = html;
    }

    async loadHistory() {
        try {
            const response = await fetch('/history');
            const data = await response.json();

            if (response.ok) {
                this.displayHistory(data);
            }
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    displayHistory(history) {
        const container = this.elements.historyList;
        
        if (!history || history.length === 0) {
            container.innerHTML = '<p class="text-center">No download history yet.</p>';
            return;
        }

        const html = history.reverse().map(item => `
            <div class="download-item">
                <h4>${item.title}</h4>
                <div class="download-meta">
                    <small>${new Date(item.downloaded_at).toLocaleString()}</small>
                    <span class="status-badge status-completed">completed</span>
                </div>
                <div class="download-details">
                    <p><strong>Quality:</strong> ${item.quality} | <strong>Type:</strong> ${item.type}</p>
                    <p><strong>File Size:</strong> ${item.file_size}</p>
                    <div class="download-actions" style="margin-top: 10px;">
                        <a href="/download_file/${item.id}" class="btn-secondary" style="text-decoration: none; font-size: 14px; padding: 8px 16px;">
                            <i class="fas fa-download"></i> Download File
                        </a>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    async loadQueue() {
        try {
            const response = await fetch('/downloads');
            const data = await response.json();

            if (response.ok) {
                this.displayQueue(data);
            }
        } catch (error) {
            console.error('Error loading queue:', error);
        }
    }

    displayQueue(downloads) {
        const container = this.elements.queueList;
        
        // Filter active downloads (not completed and not from history)
        const activeDownloads = Object.entries(downloads).filter(([id, download]) => 
            download.status !== 'completed' || 
            (download.status === 'completed' && !download.completed_at)
        );

        if (activeDownloads.length === 0) {
            container.innerHTML = '<p class="text-center">No active downloads.</p>';
            return;
        }

        const html = activeDownloads.map(([id, download]) => `
            <div class="download-item">
                <h4>${download.title || 'Processing...'}</h4>
                <div class="download-meta">
                    <small>Started: ${new Date(download.started_at).toLocaleString()}</small>
                    <span class="status-badge status-${download.status}">${download.status}</span>
                </div>
                ${download.progress !== undefined ? `
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${download.progress}%"></div>
                    </div>
                    <div class="progress-text">
                        ${download.progress}% ${download.downloaded ? `(${download.downloaded}/${download.total_size})` : ''}
                    </div>
                ` : ''}
                ${download.playlist_title ? `
                    <p><strong>Playlist:</strong> ${download.playlist_title}</p>
                    ${download.total_videos ? `<p><strong>Progress:</strong> ${download.completed_videos || 0}/${download.total_videos} videos</p>` : ''}
                ` : ''}
                ${download.error ? `<p class="error-message" style="color: var(--danger-color);">${download.error}</p>` : ''}
                <div class="download-actions" style="margin-top: 10px;">
                    <button class="btn-danger" onclick="app.deleteDownload('${id}')" style="font-size: 14px; padding: 8px 16px;">
                        <i class="fas fa-trash"></i> Cancel
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    async deleteDownload(downloadId) {
        try {
            const response = await fetch(`/delete_download/${downloadId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showToast('Download cancelled', 'success');
                this.loadQueue();
            } else {
                this.showToast('Failed to cancel download', 'error');
            }
        } catch (error) {
            this.showToast('Network error', 'error');
        }
    }

    async clearHistory() {
        if (!confirm('Are you sure you want to clear all download history?')) {
            return;
        }

        try {
            const response = await fetch('/clear_history', {
                method: 'POST'
            });

            if (response.ok) {
                this.showToast('History cleared successfully', 'success');
                this.loadHistory();
            } else {
                this.showToast('Failed to clear history', 'error');
            }
        } catch (error) {
            this.showToast('Network error', 'error');
        }
    }

    isValidYouTubeUrl(url) {
        const patterns = [
            /^https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/playlist\?list=)/,
            /^https?:\/\/(www\.)?youtube\.com\/(embed|v)\/[\w-]+/
        ];
        return patterns.some(pattern => pattern.test(url));
    }

    formatDuration(seconds) {
        if (!seconds) return '';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }

    setLoading(button, isLoading) {
        if (isLoading) {
            button.disabled = true;
            const originalText = button.innerHTML;
            button.setAttribute('data-original-text', originalText);
            button.innerHTML = '<span class="loading"></span> Loading...';
        } else {
            button.disabled = false;
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.innerHTML = originalText;
            }
        }
    }

    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;

        this.elements.toastContainer.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new YouTubeDownloader();
});