/**
 * GStreamer Media Distributor - Web Interface
 * Frontend JavaScript for managing media streams
 */

class MediaDistributor {
    constructor() {
        this.displays = [];
        this.activeStreams = [];
        this.selectedDisplays = new Set();
        this.youtubeInfo = null;
        this.currentSource = null;
        this.sourceType = 'local'; // 'local' or 'youtube'
        
        this.init();
        this.bindEvents();
        this.startPeriodicUpdates();
    }
    
    init() {
        console.log('Initializing Media Distributor interface...');
        this.loadDisplays();
        this.loadActiveStreams();
        this.checkYouTubeStatus();
    }
    
    bindEvents() {
        // Media selection change
        document.getElementById('mediaSelect').addEventListener('change', () => {
            this.sourceType = 'local';
            this.currentSource = document.getElementById('mediaSelect').value;
            this.updateStartButton();
        });
        
        // Tab changes
        const tabs = document.querySelectorAll('#sourceTab button');
        tabs.forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const target = e.target.getAttribute('data-bs-target');
                if (target === '#local') {
                    this.sourceType = 'local';
                    this.currentSource = document.getElementById('mediaSelect').value;
                } else if (target === '#youtube') {
                    this.sourceType = 'youtube';
                    this.currentSource = document.getElementById('youtubeUrl').value;
                }
                this.updateStartButton();
            });
        });
        
        // YouTube URL input
        const youtubeUrl = document.getElementById('youtubeUrl');
        if (youtubeUrl) {
            youtubeUrl.addEventListener('input', () => {
                this.currentSource = youtubeUrl.value;
                this.youtubeInfo = null;
                document.getElementById('youtubeInfo').classList.add('d-none');
                this.updateStartButton();
            });
        }
        
        // YouTube validate button
        const validateBtn = document.getElementById('validateBtn');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => {
                this.validateYouTubeUrl();
            });
        }
        
        // YouTube search
        const searchBtn = document.getElementById('doSearchBtn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.searchYouTube();
            });
        }
        
        const searchQuery = document.getElementById('searchQuery');
        if (searchQuery) {
            searchQuery.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchYouTube();
                }
            });
        }
        
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
        
        // Configuration Tab Events
        const configTab = document.getElementById('configuration-tab');
        if (configTab) {
            configTab.addEventListener('shown.bs.tab', () => {
                this.loadConfigDisplays();
                this.loadSettings();
            });
        }
        
        // Add display button
        const addDisplayBtn = document.getElementById('addDisplayBtn');
        if (addDisplayBtn) {
            addDisplayBtn.addEventListener('click', () => {
                this.addDisplay();
            });
        }
        
        // Edit display form submission
        const saveEditDisplayBtn = document.getElementById('saveEditDisplayBtn');
        if (saveEditDisplayBtn) {
            saveEditDisplayBtn.addEventListener('click', () => {
                this.saveEditDisplay();
            });
        }
        
        // Settings forms
        const streamingSettingsForm = document.getElementById('streamingSettingsForm');
        if (streamingSettingsForm) {
            streamingSettingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveStreamingSettings();
            });
        }
        
        const youtubeSettingsForm = document.getElementById('youtubeSettingsForm');
        if (youtubeSettingsForm) {
            youtubeSettingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveYouTubeSettings();
            });
        }
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
            
            // Determine source icon and label
            const sourceInfo = stream.source_type === 'youtube' ? 
                { icon: 'fab fa-youtube', label: 'YouTube', color: 'text-danger' } :
                { icon: 'fas fa-file-video', label: 'Local', color: 'text-primary' };
            
            streamCard.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title">
                                <span class="status-indicator ${statusClass}"></span>
                                <i class="${sourceInfo.icon} ${sourceInfo.color} me-1"></i>
                                ${stream.media_source}
                            </h6>
                            <p class="card-text text-muted mb-2">
                                <span class="badge bg-secondary me-2">${sourceInfo.label}</span>
                                <i class="fas fa-tv me-1"></i>${stream.displays} displays
                                <i class="fas fa-clock ms-3 me-1"></i>${uptime}
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
        let mediaSource, sourceData;
        
        if (this.sourceType === 'local') {
            const mediaSelect = document.getElementById('mediaSelect');
            mediaSource = mediaSelect.value;
            
            if (!mediaSource) {
                this.showToast('Please select a media file', 'warning');
                return;
            }
            
            sourceData = {
                file: mediaSource,
                type: 'local'
            };
        } else if (this.sourceType === 'youtube') {
            const youtubeUrl = document.getElementById('youtubeUrl');
            mediaSource = youtubeUrl.value;
            
            if (!mediaSource) {
                this.showToast('Please enter a YouTube URL', 'warning');
                return;
            }
            
            if (!this.youtubeInfo) {
                this.showToast('Please validate the YouTube URL first', 'warning');
                return;
            }
            
            sourceData = {
                url: mediaSource,
                type: 'youtube'
            };
        }
        
        if (this.selectedDisplays.size === 0) {
            this.showToast('Please select at least one display', 'warning');
            return;
        }
        
        const displays = Array.from(this.selectedDisplays);
        const streamData = {
            ...sourceData,
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
                this.showToast(`Stream started: ${this.sourceType === 'youtube' ? this.youtubeInfo?.title || 'YouTube video' : mediaSource}`, 'success');
                
                // Reset form
                if (this.sourceType === 'local') {
                    document.getElementById('mediaSelect').value = '';
                } else {
                    document.getElementById('youtubeUrl').value = '';
                    document.getElementById('youtubeInfo').classList.add('d-none');
                    this.youtubeInfo = null;
                }
                
                this.currentSource = null;
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
        const startBtn = document.getElementById('startStreamBtn');
        
        let hasSource = false;
        if (this.sourceType === 'local') {
            const mediaSelect = document.getElementById('mediaSelect');
            hasSource = mediaSelect.value !== '';
        } else if (this.sourceType === 'youtube') {
            const youtubeUrl = document.getElementById('youtubeUrl');
            hasSource = youtubeUrl.value !== '' && this.youtubeInfo !== null;
        }
        
        const hasDisplays = this.selectedDisplays.size > 0;
        
        startBtn.disabled = !hasSource || !hasDisplays;
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
    
    // YouTube-specific methods
    async checkYouTubeStatus() {
        try {
            const response = await fetch('/api/youtube/status');
            const data = await response.json();
            
            if (!data.enabled) {
                // Hide YouTube tab if not enabled
                const youtubeTab = document.getElementById('youtube-tab');
                if (youtubeTab) {
                    youtubeTab.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error checking YouTube status:', error);
        }
    }
    
    async validateYouTubeUrl() {
        const youtubeUrl = document.getElementById('youtubeUrl');
        const validateBtn = document.getElementById('validateBtn');
        const url = youtubeUrl.value.trim();
        
        if (!url) {
            this.showToast('Please enter a YouTube URL', 'warning');
            return;
        }
        
        try {
            // Show loading state
            validateBtn.disabled = true;
            validateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            const response = await fetch('/api/youtube/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.youtubeInfo = data.info;
                this.displayYouTubeInfo(data.info);
                this.showToast('YouTube URL validated successfully', 'success');
                this.updateStartButton();
            } else {
                this.youtubeInfo = null;
                document.getElementById('youtubeInfo').classList.add('d-none');
                this.showToast(data.message || 'Invalid YouTube URL', 'error');
                this.updateStartButton();
            }
        } catch (error) {
            console.error('Error validating YouTube URL:', error);
            this.showToast('Error validating YouTube URL', 'error');
        } finally {
            validateBtn.disabled = false;
            validateBtn.innerHTML = '<i class="fas fa-check"></i>';
        }
    }
    
    displayYouTubeInfo(info) {
        const infoDiv = document.getElementById('youtubeInfo');
        const thumbnail = document.getElementById('youtubeThumbnail');
        const title = document.getElementById('youtubeTitle');
        const uploader = document.getElementById('youtubeUploader');
        const duration = document.getElementById('youtubeDuration');
        
        thumbnail.src = info.thumbnail || '';
        title.textContent = info.title || 'Unknown Title';
        uploader.textContent = `By: ${info.uploader || 'Unknown'}`;
        
        if (info.duration) {
            const minutes = Math.floor(info.duration / 60);
            const seconds = info.duration % 60;
            duration.textContent = `Duration: ${minutes}:${seconds.toString().padStart(2, '0')}`;
        } else {
            duration.textContent = 'Duration: Unknown';
        }
        
        infoDiv.classList.remove('d-none');
    }
    
    async searchYouTube() {
        const searchQuery = document.getElementById('searchQuery');
        const searchBtn = document.getElementById('doSearchBtn');
        const resultsDiv = document.getElementById('searchResults');
        const query = searchQuery.value.trim();
        
        if (!query) {
            this.showToast('Please enter a search term', 'warning');
            return;
        }
        
        try {
            // Show loading state
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
            
            resultsDiv.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
                    <p>Searching YouTube...</p>
                </div>
            `;
            
            const response = await fetch('/api/youtube/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query, max_results: 8 })
            });
            
            const data = await response.json();
            
            if (data.success && data.results.length > 0) {
                this.displaySearchResults(data.results);
            } else {
                resultsDiv.innerHTML = `
                    <div class="text-center text-muted py-4">
                        <i class="fas fa-search fa-3x mb-3"></i>
                        <p>No results found</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error searching YouTube:', error);
            resultsDiv.innerHTML = `
                <div class="text-center text-danger py-4">
                    <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
                    <p>Search failed</p>
                </div>
            `;
        } finally {
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="fas fa-search"></i> Search';
        }
    }
    
    displaySearchResults(results) {
        const resultsDiv = document.getElementById('searchResults');
        
        let html = '<div class="row">';
        results.forEach(video => {
            const duration = video.duration ? 
                `${Math.floor(video.duration / 60)}:${(video.duration % 60).toString().padStart(2, '0')}` : 
                'N/A';
            
            html += `
                <div class="col-md-6 mb-3">
                    <div class="card h-100 search-result-card" data-url="${video.url}">
                        <div class="card-body p-3">
                            <h6 class="card-title mb-2" style="font-size: 0.9em; line-height: 1.2;">${video.title}</h6>
                            <small class="text-muted">
                                <div>By: ${video.uploader || 'Unknown'}</div>
                                <div>Duration: ${duration}</div>
                                ${video.view_count ? `<div>Views: ${video.view_count.toLocaleString()}</div>` : ''}
                            </small>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        resultsDiv.innerHTML = html;
        
        // Add click handlers
        document.querySelectorAll('.search-result-card').forEach(card => {
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => {
                const url = card.dataset.url;
                document.getElementById('youtubeUrl').value = url;
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('searchModal'));
                modal.hide();
                
                // Switch to YouTube tab
                const youtubeTab = document.getElementById('youtube-tab');
                youtubeTab.click();
                
                // Validate the selected URL
                setTimeout(() => {
                    this.validateYouTubeUrl();
                }, 500);
            });
            
            card.addEventListener('mouseenter', () => {
                card.style.backgroundColor = '#f8f9fa';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.backgroundColor = '';
            });
        });
    }
    
    // Configuration Management Methods
    async loadConfigDisplays() {
        try {
            const response = await fetch('/api/config/displays');
            const data = await response.json();
            
            if (data.success) {
                this.renderConfigDisplaysTable(data.displays);
            } else {
                this.showToast('Failed to load display configuration', 'error');
            }
        } catch (error) {
            console.error('Error loading display config:', error);
            this.showToast('Error loading display configuration', 'error');
        }
    }
    
    renderConfigDisplaysTable(displays) {
        const tbody = document.getElementById('displaysTable');
        tbody.innerHTML = '';
        
        displays.forEach(display => {
            const row = document.createElement('tr');
            const statusBadge = display.enabled ? 
                '<span class="badge bg-success">Enabled</span>' : 
                '<span class="badge bg-secondary">Disabled</span>';
                
            row.innerHTML = `
                <td>${display.name}</td>
                <td>${display.ip}</td>
                <td>${display.port}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="app.editDisplay('${display.name}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="app.deleteDisplay('${display.name}')">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }
    
    async addDisplay() {
        const name = document.getElementById('newDisplayName').value.trim();
        const ip = document.getElementById('newDisplayIP').value.trim();
        const port = parseInt(document.getElementById('newDisplayPort').value) || 5000;
        
        if (!name || !ip) {
            this.showToast('Name and IP address are required', 'error');
            return;
        }
        
        const displayData = {
            name: name,
            ip: ip,
            port: port,
            enabled: true
        };
        
        try {
            const response = await fetch('/api/config/displays', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(displayData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast(`Display "${name}" added successfully`, 'success');
                // Clear form
                document.getElementById('newDisplayName').value = '';
                document.getElementById('newDisplayIP').value = '';
                document.getElementById('newDisplayPort').value = '5000';
                // Reload displays
                this.loadConfigDisplays();
                this.loadDisplays(); // Also refresh the streaming displays
            } else {
                this.showToast(data.message || 'Failed to add display', 'error');
            }
        } catch (error) {
            console.error('Error adding display:', error);
            this.showToast('Error adding display', 'error');
        }
    }
    
    async editDisplay(displayName) {
        try {
            const response = await fetch('/api/config/displays');
            const data = await response.json();
            
            if (data.success) {
                const display = data.displays.find(d => d.name === displayName);
                if (display) {
                    // Fill the edit form
                    document.getElementById('editDisplayOriginalName').value = display.name;
                    document.getElementById('editDisplayName').value = display.name;
                    document.getElementById('editDisplayIP').value = display.ip;
                    document.getElementById('editDisplayPort').value = display.port;
                    document.getElementById('editDisplayEnabled').checked = display.enabled;
                    
                    // Show modal
                    const modal = new bootstrap.Modal(document.getElementById('editDisplayModal'));
                    modal.show();
                }
            }
        } catch (error) {
            console.error('Error loading display for edit:', error);
            this.showToast('Error loading display information', 'error');
        }
    }
    
    async saveEditDisplay() {
        const originalName = document.getElementById('editDisplayOriginalName').value;
        const name = document.getElementById('editDisplayName').value.trim();
        const ip = document.getElementById('editDisplayIP').value.trim();
        const port = parseInt(document.getElementById('editDisplayPort').value) || 5000;
        const enabled = document.getElementById('editDisplayEnabled').checked;
        
        if (!name || !ip) {
            this.showToast('Name and IP address are required', 'error');
            return;
        }
        
        const displayData = {
            name: name,
            ip: ip,
            port: port,
            enabled: enabled
        };
        
        try {
            const response = await fetch(`/api/config/displays/${originalName}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(displayData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast(`Display "${originalName}" updated successfully`, 'success');
                
                // Hide modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('editDisplayModal'));
                modal.hide();
                
                // Reload displays
                this.loadConfigDisplays();
                this.loadDisplays(); // Also refresh the streaming displays
            } else {
                this.showToast(data.message || 'Failed to update display', 'error');
            }
        } catch (error) {
            console.error('Error updating display:', error);
            this.showToast('Error updating display', 'error');
        }
    }
    
    async deleteDisplay(displayName) {
        if (!confirm(`Are you sure you want to delete display "${displayName}"?`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/config/displays/${displayName}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast(`Display "${displayName}" deleted successfully`, 'success');
                this.loadConfigDisplays();
                this.loadDisplays(); // Also refresh the streaming displays
            } else {
                this.showToast(data.message || 'Failed to delete display', 'error');
            }
        } catch (error) {
            console.error('Error deleting display:', error);
            this.showToast('Error deleting display', 'error');
        }
    }
    
    async loadSettings() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();
            
            if (data.success) {
                const config = data.config;
                
                // Load streaming settings
                const streaming = config.streaming || {};
                document.getElementById('defaultBitrate').value = streaming.bitrate || 2000;
                document.getElementById('videoCodec').value = streaming.video_codec || 'x264enc';
                document.getElementById('audioCodec').value = streaming.audio_codec || 'lamemp3enc';
                
                // Load YouTube settings
                const youtube = config.youtube || {};
                const youtubeQuality = document.getElementById('youtubeQuality');
                if (youtubeQuality) {
                    youtubeQuality.value = youtube.default_quality || '720p';
                }
                const maxDuration = document.getElementById('maxDuration');
                if (maxDuration) {
                    maxDuration.value = youtube.max_duration || 7200;
                }
                const cacheSize = document.getElementById('cacheSize');
                if (cacheSize) {
                    cacheSize.value = youtube.cache_size || 100;
                }
            }
        } catch (error) {
            console.error('Error loading settings:', error);
            this.showToast('Error loading settings', 'error');
        }
    }
    
    async saveStreamingSettings() {
        const settings = {
            streaming: {
                bitrate: parseInt(document.getElementById('defaultBitrate').value) || 2000,
                video_codec: document.getElementById('videoCodec').value,
                audio_codec: document.getElementById('audioCodec').value
            }
        };
        
        try {
            const response = await fetch('/api/config/settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Streaming settings saved successfully', 'success');
            } else {
                this.showToast(data.message || 'Failed to save settings', 'error');
            }
        } catch (error) {
            console.error('Error saving streaming settings:', error);
            this.showToast('Error saving streaming settings', 'error');
        }
    }
    
    async saveYouTubeSettings() {
        const settings = {
            youtube: {
                default_quality: document.getElementById('youtubeQuality').value,
                max_duration: parseInt(document.getElementById('maxDuration').value) || 7200,
                cache_size: parseInt(document.getElementById('cacheSize').value) || 100
            }
        };
        
        try {
            const response = await fetch('/api/config/settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('YouTube settings saved successfully', 'success');
            } else {
                this.showToast(data.message || 'Failed to save YouTube settings', 'error');
            }
        } catch (error) {
            console.error('Error saving YouTube settings:', error);
            this.showToast('Error saving YouTube settings', 'error');
        }
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new MediaDistributor();
});
