/**
 * GStreamer Media Distributor - Web Interface
 * Frontend JavaScript for managing media streams
 */

class MediaDistributor {
    constructor() {
        this.displays = [];
        this.activeStreams = [];
        this.selectedDisplays = new Set();
        
        this.init();
        this.bindEvents();
        this.startPeriodicUpdates();
    }
    
    init() {
        console.log('Initializing Media Distributor interface...');
        this.loadDisplays();
        this.loadActiveStreams();
    }
    
    bindEvents() {
        // Media selection change
        document.getElementById('mediaSelect').addEventListener('change', () => {
            this.updateStartButton();
        });
        
        // Start stream button
        document.getElementById('startStreamBtn').addEventListener('click', () => {
            this.startStream();
        });
        
        // Refresh buttons
        document.getElementById('refreshBtn').addEventListener('click', () => {
            location.reload();
        });
        
        document.getElementById('refreshStreamsBtn').addEventListener('click', () => {
            this.loadActiveStreams();
        });
    }
    
    async loadDisplays() {
        try {
            const response = await fetch('/api/displays');
            const data = await response.json();
            
            if (data.success) {
                this.displays = data.displays;
                this.renderDisplays();
                this.updateDisplayCount();
            } else {
                this.showToast('Failed to load displays', 'error');
            }
        } catch (error) {
            console.error('Error loading displays:', error);
            this.showToast('Error loading displays', 'error');
        }
    }
    
    renderDisplays() {
        const container = document.getElementById('displaysList');
        container.innerHTML = '';
        
        this.displays.forEach(display => {
            const displayDiv = document.createElement('div');
            displayDiv.className = 'form-check mb-2';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'form-check-input';
            checkbox.id = `display-${display.name.replace(/\s+/g, '-')}`;
            checkbox.value = JSON.stringify(display);
            checkbox.checked = display.enabled;
            
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedDisplays.add(display);
                } else {
                    this.selectedDisplays.delete(display);
                }
                this.updateStartButton();
            });
            
            const label = document.createElement('label');
            label.className = 'form-check-label d-flex justify-content-between align-items-center w-100';
            label.htmlFor = checkbox.id;
            
            const statusClass = display.enabled ? 'status-running' : 'status-stopped';
            label.innerHTML = `
                <span>
                    <span class="status-indicator ${statusClass}"></span>
                    ${display.name}
                </span>
                <small class="text-muted">${display.ip}:${display.port}</small>
            `;
            
            displayDiv.appendChild(checkbox);
            displayDiv.appendChild(label);
            container.appendChild(displayDiv);
            
            // Pre-select enabled displays
            if (display.enabled) {
                this.selectedDisplays.add(display);
            }
        });
        
        this.updateStartButton();
    }
    
    async loadActiveStreams() {
        try {
            const response = await fetch('/api/streams');
            const data = await response.json();
            
            if (data.success) {
                this.activeStreams = data.streams;
                this.renderActiveStreams();
                this.updateStreamCount();
            }
        } catch (error) {
            console.error('Error loading streams:', error);
        }
    }
    
    renderActiveStreams() {
        const container = document.getElementById('activeStreams');
        
        if (this.activeStreams.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-stream fa-3x mb-3"></i>
                    <p>No active streams</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        this.activeStreams.forEach(stream => {
            const streamCard = document.createElement('div');
            streamCard.className = 'card stream-card mb-3';
            
            const statusClass = stream.running ? 'status-running' : 'status-stopped';
            const uptime = this.formatUptime(stream.uptime);
            
            streamCard.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title">
                                <span class="status-indicator ${statusClass}"></span>
                                ${stream.media_file}
                            </h6>
                            <p class="card-text text-muted mb-2">
                                <i class="fas fa-tv me-2"></i>${stream.displays} displays
                                <i class="fas fa-clock ms-3 me-2"></i>${uptime}
                            </p>
                            <small class="text-muted">Stream ID: ${stream.stream_id}</small>
                        </div>
                        <div>
                            <button class="btn btn-sm btn-outline-danger" onclick="app.stopStream('${stream.stream_id}')">
                                <i class="fas fa-stop"></i> Stop
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            container.appendChild(streamCard);
        });
    }
    
    async startStream() {
        const mediaSelect = document.getElementById('mediaSelect');
        const selectedMedia = mediaSelect.value;
        
        if (!selectedMedia) {
            this.showToast('Please select a media file', 'warning');
            return;
        }
        
        if (this.selectedDisplays.size === 0) {
            this.showToast('Please select at least one display', 'warning');
            return;
        }
        
        const displays = Array.from(this.selectedDisplays);
        const streamData = {
            file: selectedMedia,
            displays: displays
        };
        
        try {
            this.setLoading(true);
            const response = await fetch('/api/stream/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(streamData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast(`Stream started: ${selectedMedia}`, 'success');
                mediaSelect.value = '';
                this.updateStartButton();
                
                // Refresh streams after a short delay
                setTimeout(() => {
                    this.loadActiveStreams();
                }, 1000);
            } else {
                this.showToast(data.message || 'Failed to start stream', 'error');
            }
        } catch (error) {
            console.error('Error starting stream:', error);
            this.showToast('Error starting stream', 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    async stopStream(streamId) {
        if (!confirm('Are you sure you want to stop this stream?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/stream/stop/${streamId}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Stream stopped', 'success');
                this.loadActiveStreams();
            } else {
                this.showToast(data.message || 'Failed to stop stream', 'error');
            }
        } catch (error) {
            console.error('Error stopping stream:', error);
            this.showToast('Error stopping stream', 'error');
        }
    }
    
    updateStartButton() {
        const mediaSelect = document.getElementById('mediaSelect');
        const startBtn = document.getElementById('startStreamBtn');
        
        const hasMedia = mediaSelect.value !== '';
        const hasDisplays = this.selectedDisplays.size > 0;
        
        startBtn.disabled = !hasMedia || !hasDisplays;
    }
    
    updateStreamCount() {
        document.getElementById('totalStreams').textContent = this.activeStreams.length;
    }
    
    updateDisplayCount() {
        const enabledDisplays = this.displays.filter(d => d.enabled).length;
        document.getElementById('totalDisplays').textContent = enabledDisplays;
    }
    
    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
    
    setLoading(loading) {
        const startBtn = document.getElementById('startStreamBtn');
        const statusBadge = document.getElementById('status-badge');
        
        if (loading) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Starting...';
            statusBadge.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Starting Stream';
            statusBadge.className = 'badge bg-warning me-2';
        } else {
            this.updateStartButton();
            startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Start Stream';
            statusBadge.innerHTML = '<i class="fas fa-circle me-1"></i>Ready';
            statusBadge.className = 'badge bg-success me-2';
        }
    }
    
    showToast(message, type = 'info') {
        const toast = document.getElementById('notification-toast');
        const toastBody = document.getElementById('toast-message');
        
        // Set message and style based on type
        toastBody.textContent = message;
        
        const toastBootstrap = new bootstrap.Toast(toast);
        toastBootstrap.show();
    }
    
    startPeriodicUpdates() {
        // Update active streams every 5 seconds
        setInterval(() => {
            this.loadActiveStreams();
        }, 5000);
        
        // Update system status every 10 seconds
        setInterval(() => {
            this.updateSystemStatus();
        }, 10000);
    }
    
    async updateSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('systemStatus').textContent = data.status;
                
                // Update status badge color based on health
                const statusCard = document.getElementById('systemStatus').parentElement.parentElement;
                statusCard.className = `card bg-${data.status === 'OK' ? 'warning' : 'danger'} text-white`;
            }
        } catch (error) {
            console.error('Error updating system status:', error);
        }
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new MediaDistributor();
});
