/**
 * Sinhala Fingerspelling Web Application
 * Interactive JavaScript for managing fingerspelling visualization
 */

class FingerspellingApp {
    constructor() {
        this.currentVideoIndex = 0;
        this.videoSequence = [];
        this.isPlaying = false;
        this.currentVideo = null;
        this.playbackSpeed = 1.0;
        this.currentTab = 'text';
        
        this.initializeEventListeners();
        this.loadSampleWords();
    }

    initializeEventListeners() {
        // Tab switching
        document.getElementById('textTab').addEventListener('click', () => this.switchTab('text'));
        document.getElementById('numberTab').addEventListener('click', () => this.switchTab('number'));
        
        // Convert buttons
        document.getElementById('convertBtn').addEventListener('click', () => this.convertWord());
        document.getElementById('convertNumberBtn').addEventListener('click', () => this.convertNumber());
        
        // Concatenation buttons
        document.getElementById('concatenateTextBtn').addEventListener('click', () => this.concatenateText());
        document.getElementById('concatenateNumberBtn').addEventListener('click', () => this.concatenateNumber());
        
        // Enter key on inputs
        document.getElementById('wordInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.convertWord();
            }
        });
        
        document.getElementById('numberInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.convertNumber();
            }
        });

        // Video controls
        document.getElementById('playAllBtn').addEventListener('click', () => this.playAllVideos());
        document.getElementById('pauseBtn').addEventListener('click', () => this.pauseVideos());
        document.getElementById('resetBtn').addEventListener('click', () => this.resetVideos());
        
        // Playback speed
        document.getElementById('playbackSpeed').addEventListener('change', (e) => {
            this.playbackSpeed = parseFloat(e.target.value);
            if (this.currentVideo) {
                this.currentVideo.playbackRate = this.playbackSpeed;
            }
        });

        // Sample numbers
        document.querySelectorAll('.sample-number').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const number = e.target.dataset.number;
                document.getElementById('numberInput').value = number;
                this.convertNumber();
            });
        });

        // Download concatenated video
        document.getElementById('downloadVideoBtn').addEventListener('click', () => this.downloadConcatenatedVideo());

        // Statistics modal
        document.getElementById('showStatsBtn').addEventListener('click', () => this.showStatistics());
        document.getElementById('closeStatsModal').addEventListener('click', () => this.hideStatistics());
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        if (tabName === 'text') {
            document.getElementById('textTab').classList.add('active');
            document.getElementById('textTabContent').classList.add('active');
        } else {
            document.getElementById('numberTab').classList.add('active');
            document.getElementById('numberTabContent').classList.add('active');
        }
        
        this.currentTab = tabName;
        this.hideResults();
        this.hideConcatenatedVideo();
    }

    async loadSampleWords() {
        try {
            const response = await fetch('/api/samples');
            const data = await response.json();
            
            if (data.success) {
                this.displaySampleWords(data.samples);
            }
        } catch (error) {
            console.error('Error loading samples:', error);
        }
    }

    displaySampleWords(samples) {
        const container = document.getElementById('sampleWords');
        container.innerHTML = '';

        // Combine names and villages for display
        const allSamples = [...(samples.names || []), ...(samples.villages || [])];
        
        allSamples.slice(0, 8).forEach(word => {
            const button = document.createElement('button');
            button.className = 'sample-word sinhala-text';
            button.textContent = word;
            button.addEventListener('click', () => {
                document.getElementById('wordInput').value = word;
                this.convertWord();
            });
            container.appendChild(button);
        });
    }

    async convertNumber() {
        const input = document.getElementById('numberInput').value.trim();
        
        if (!input) {
            this.showError('Please enter a number');
            return;
        }

        this.showLoading();
        this.hideError();
        this.hideResults();
        this.hideConcatenatedVideo();

        try {
            const response = await fetch('/api/convert-number', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ number: input })
            });

            const data = await response.json();

            if (data.success) {
                this.displayResults(data, 'number');
            } else {
                this.showError(data.error || 'Number conversion failed');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async concatenateText() {
        const input = document.getElementById('wordInput').value.trim();
        
        if (!input) {
            this.showError('Please enter text first');
            return;
        }

        await this.requestConcatenation(input, 'text');
    }

    async concatenateNumber() {
        const input = document.getElementById('numberInput').value.trim();
        
        if (!input) {
            this.showError('Please enter a number first');
            return;
        }

        await this.requestConcatenation(input, 'number');
    }

    async requestConcatenation(input, type) {
        this.showLoading();
        this.hideError();

        try {
            const body = type === 'text' ? { text: input, type: 'text' } : { number: input, type: 'number' };
            
            const response = await fetch('/api/concatenate-video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(body)
            });

            const data = await response.json();

            if (data.success && data.concatenated_video && data.concatenated_video.success) {
                this.displayConcatenatedVideo(data.concatenated_video, input);
            } else {
                // If concatenation fails, try to create a playlist for sequential playback
                console.log('Concatenation failed, trying playlist approach...');
                this.createVideoPlaylist(input, type);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displayConcatenatedVideo(videoData, inputText) {
        const section = document.getElementById('concatenatedVideoSection');
        const player = document.getElementById('concatenatedVideoPlayer');
        const info = document.getElementById('concatenationInfo');
        
        // Show the section
        section.classList.remove('hidden');
        
        // Set video source
        const videoPath = videoData.video_path.replace(/\\/g, '/');
        const videoUrl = '/concatenated-videos/' + videoPath.split('/').pop();
        player.src = videoUrl;
        
        // Update info
        info.innerHTML = `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div>
                    <span class="font-semibold text-gray-800">${inputText}</span>
                    <div class="text-xs text-gray-600">Input</div>
                </div>
                <div>
                    <span class="font-semibold text-green-600">${videoData.video_count}</span>
                    <div class="text-xs text-gray-600">Videos Used</div>
                </div>
                <div>
                    <span class="font-semibold text-red-600">${videoData.missing_count || 0}</span>
                    <div class="text-xs text-gray-600">Missing Videos</div>
                </div>
                <div>
                    <span class="font-semibold ${videoData.cached ? 'text-blue-600' : 'text-green-600'}">
                        ${videoData.cached ? 'Cached' : 'Generated'}
                    </span>
                    <div class="text-xs text-gray-600">Status</div>
                </div>
            </div>
        `;
        
        // Scroll to video
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    hideConcatenatedVideo() {
        document.getElementById('concatenatedVideoSection').classList.add('hidden');
    }

    downloadConcatenatedVideo() {
        const player = document.getElementById('concatenatedVideoPlayer');
        if (player.src) {
            const a = document.createElement('a');
            a.href = player.src;
            a.download = 'fingerspelling_video.mp4';
            a.click();
        }
    }

    async convertWord() {
        const input = document.getElementById('wordInput').value.trim();
        
        if (!input) {
            this.showError('Please enter a Sinhala word');
            return;
        }

        this.showLoading();
        this.hideError();
        this.hideResults();

        try {
            const response = await fetch('/api/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: input })
            });

            const data = await response.json();

            if (data.success) {
                this.displayResults(data);
            } else {
                this.showError(data.error || 'Conversion failed');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displayResults(data, type = 'text') {
        // Update analysis cards
        const inputField = type === 'text' ? 'input_word' : 'input_number';
        document.getElementById('inputWord').textContent = data[inputField] || data.input_word;
        document.getElementById('signCount').textContent = data.signs?.length || 0;
        document.getElementById('videoCount').textContent = 
            data.video_urls?.filter(v => v.url).length || 0;

        // Display signs
        this.displaySigns(data.signs || []);
        
        // Setup video sequence
        this.setupVideoSequence(data.video_urls || []);
        
        // Show results
        this.showResults();
    }

    displaySigns(signs) {
        const container = document.getElementById('signsList');
        container.innerHTML = '';

        signs.forEach((sign, index) => {
            const badge = document.createElement('div');
            badge.className = 'sign-badge sinhala-text';
            badge.textContent = sign;
            badge.title = `Sign ${index + 1}: ${sign}`;
            container.appendChild(badge);
        });
    }

    setupVideoSequence(videoUrls) {
        this.videoSequence = videoUrls;
        this.currentVideoIndex = 0;
        
        const container = document.getElementById('videoSequence');
        container.innerHTML = '';

        videoUrls.forEach((videoData, index) => {
            const item = document.createElement('div');
            item.className = 'video-item';
            item.dataset.index = index;

            const hasVideo = videoData.url && !videoData.error;
            
            item.innerHTML = `
                <div class="text-center">
                    <div class="text-lg font-semibold sinhala-text mb-2">${videoData.sign}</div>
                    <div class="text-sm ${hasVideo ? 'text-green-600' : 'text-red-600'}">
                        <i class="fas ${hasVideo ? 'fa-check-circle' : 'fa-times-circle'} mr-1"></i>
                        ${hasVideo ? 'Available' : 'Missing'}
                    </div>
                    ${!hasVideo ? `<div class="text-xs text-red-500 mt-1">${videoData.error || 'Video not found'}</div>` : ''}
                </div>
            `;

            if (hasVideo) {
                item.addEventListener('click', () => this.playVideoAtIndex(index));
                item.style.cursor = 'pointer';
            } else {
                item.classList.add('error');
            }

            container.appendChild(item);
        });
    }

    async playAllVideos() {
        if (this.videoSequence.length === 0) return;

        this.isPlaying = true;
        this.currentVideoIndex = 0;
        
        // Update UI
        document.getElementById('playAllBtn').disabled = true;
        document.getElementById('currentVideoInfo').classList.remove('hidden');

        await this.playVideoSequence();
    }

    async playVideoSequence() {
        while (this.currentVideoIndex < this.videoSequence.length && this.isPlaying) {
            const videoData = this.videoSequence[this.currentVideoIndex];
            
            if (videoData.url && !videoData.error) {
                await this.playVideo(videoData, this.currentVideoIndex);
            }
            
            this.currentVideoIndex++;
        }

        // Reset UI when finished
        this.isPlaying = false;
        document.getElementById('playAllBtn').disabled = false;
        this.updateVideoProgress();
    }

    async playVideo(videoData, index) {
        return new Promise((resolve, reject) => {
            // Update UI to show current video
            this.updateVideoUI(videoData, index);
            
            const videoPlayer = document.getElementById('videoPlayer');
            
            // Create video element
            const video = document.createElement('video');
            video.className = 'video-player';
            video.controls = true;
            video.autoplay = true;
            video.playbackRate = this.playbackSpeed;
            video.src = videoData.url;

            // Clear previous content and add video
            videoPlayer.innerHTML = '';
            videoPlayer.appendChild(video);

            this.currentVideo = video;

            // Handle video events
            video.addEventListener('loadeddata', () => {
                video.play().catch(e => {
                    console.error('Error playing video:', e);
                    resolve();
                });
            });

            video.addEventListener('ended', () => {
                this.markVideoAsPlayed(index);
                resolve();
            });

            video.addEventListener('error', (e) => {
                console.error('Video error:', e);
                this.showVideoError(videoData.sign);
                resolve();
            });

            // Fallback timeout
            setTimeout(() => {
                resolve();
            }, 10000); // 10 second timeout
        });
    }

    async playVideoAtIndex(index) {
        if (index >= 0 && index < this.videoSequence.length) {
            const videoData = this.videoSequence[index];
            if (videoData.url && !videoData.error) {
                this.currentVideoIndex = index;
                document.getElementById('currentVideoInfo').classList.remove('hidden');
                await this.playVideo(videoData, index);
                this.updateVideoProgress();
            }
        }
    }

    updateVideoUI(videoData, index) {
        // Update current sign display
        document.getElementById('currentSign').textContent = videoData.sign;
        
        // Update video items
        document.querySelectorAll('.video-item').forEach((item, i) => {
            item.classList.remove('playing');
            if (i === index) {
                item.classList.add('playing');
            }
        });

        this.updateVideoProgress();
    }

    updateVideoProgress() {
        const progressText = `${this.currentVideoIndex + 1} / ${this.videoSequence.length}`;
        document.getElementById('videoProgress').textContent = progressText;
    }

    markVideoAsPlayed(index) {
        const videoItem = document.querySelector(`.video-item[data-index="${index}"]`);
        if (videoItem) {
            videoItem.classList.add('played');
            videoItem.classList.remove('playing');
        }
    }

    pauseVideos() {
        this.isPlaying = false;
        if (this.currentVideo) {
            this.currentVideo.pause();
        }
        document.getElementById('playAllBtn').disabled = false;
    }

    resetVideos() {
        this.isPlaying = false;
        this.currentVideoIndex = 0;
        
        if (this.currentVideo) {
            this.currentVideo.pause();
            this.currentVideo.currentTime = 0;
        }

        // Reset UI
        document.getElementById('videoPlayer').innerHTML = `
            <div class="text-gray-500 flex flex-col items-center justify-center h-full">
                <i class="fas fa-play-circle text-6xl mb-4"></i>
                <p>Click "Play All" to start the fingerspelling sequence</p>
            </div>
        `;

        document.getElementById('currentVideoInfo').classList.add('hidden');
        document.getElementById('playAllBtn').disabled = false;

        // Reset video items
        document.querySelectorAll('.video-item').forEach(item => {
            item.classList.remove('playing', 'played');
        });
    }

    showVideoError(sign) {
        const videoPlayer = document.getElementById('videoPlayer');
        videoPlayer.innerHTML = `
            <div class="text-center text-red-500 flex flex-col items-center justify-center h-full">
                <i class="fas fa-exclamation-triangle text-6xl mb-4"></i>
                <p>Error playing video for sign: <span class="sinhala-text font-semibold">${sign}</span></p>
                <p class="text-sm mt-2">Continuing to next video...</p>
            </div>
        `;
    }

    async showStatistics() {
        try {
            const response = await fetch('/api/statistics');
            const data = await response.json();

            if (data.success) {
                this.displayStatistics(data.statistics);
                document.getElementById('statsModal').classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    displayStatistics(stats) {
        const content = document.getElementById('statsContent');
        const videoStats = stats.video_statistics;
        const converterStats = stats.converter_rules;

        content.innerHTML = `
            <div class="space-y-6">
                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-blue-50 rounded-lg p-4">
                        <div class="text-2xl font-bold text-blue-600">${videoStats.total_mappings}</div>
                        <div class="text-sm text-blue-600">Total Video Mappings</div>
                    </div>
                    <div class="bg-green-50 rounded-lg p-4">
                        <div class="text-2xl font-bold text-green-600">${videoStats.existing_videos}</div>
                        <div class="text-sm text-green-600">Available Videos</div>
                    </div>
                    <div class="bg-red-50 rounded-lg p-4">
                        <div class="text-2xl font-bold text-red-600">${videoStats.missing_videos}</div>
                        <div class="text-sm text-red-600">Missing Videos</div>
                    </div>
                    <div class="bg-purple-50 rounded-lg p-4">
                        <div class="text-2xl font-bold text-purple-600">${videoStats.coverage_percentage.toFixed(1)}%</div>
                        <div class="text-sm text-purple-600">Coverage</div>
                    </div>
                </div>
                
                <div>
                    <h4 class="font-semibold text-gray-700 mb-2">Converter Rules</h4>
                    <div class="bg-gray-50 rounded-lg p-4">
                        <div class="text-sm space-y-1">
                            <div>Total Allowed Signs: <span class="font-semibold">${converterStats.total_allowed_signs}</span></div>
                            <div>Vowel Mappings: <span class="font-semibold">${converterStats.vowel_mappings}</span></div>
                            <div>Available Signs: <span class="font-semibold">${stats.available_signs_count}</span></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    hideStatistics() {
        document.getElementById('statsModal').classList.add('hidden');
    }

    showLoading() {
        document.getElementById('loadingState').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingState').classList.add('hidden');
    }

    // Create a playlist for sequential video playback when concatenation is unavailable
    async createVideoPlaylist(input, type) {
        try {
            const body = type === 'text' ? { text: input, type: 'text' } : { number: input, type: 'number' };
            
            console.log('Creating video playlist for:', input, 'type:', type);
            console.log('Request body:', body);
            
            const response = await fetch('/api/video-playlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            
            const data = await response.json();
            
            console.log('Playlist API response:', data);
            console.log('Success:', data.success);
            console.log('Videos:', data.videos);
            console.log('Videos length:', data.videos ? data.videos.length : 'undefined');
            
            // Filter out videos with null URLs or errors
            const validVideos = data.videos ? data.videos.filter(video => video.url && !video.error) : [];
            console.log('Valid videos:', validVideos.length, 'out of', data.videos ? data.videos.length : 0);
            
            if (data.success && validVideos.length > 0) {
                console.log('Displaying video playlist...');
                // Ensure results section is visible before displaying playlist
                this.showResults();
                this.displayVideoPlaylist(validVideos, input);
            } else {
                console.log('Playlist creation failed - showing error message');
                this.showError('Could not create video playlist. You can still watch individual videos by clicking "Play All" below.');
            }
        } catch (error) {
            console.error('Playlist creation error:', error);
            this.showError('Video playlist creation failed. You can still watch individual videos by clicking "Play All" below.');
        }
    }
    
    // Display sequential video playlist
    displayVideoPlaylist(videos, input) {
        try {
            console.log('Displaying playlist with', videos.length, 'videos');
            console.log('First video:', videos[0]);
            
            if (!videos || videos.length === 0) {
                throw new Error('No videos to display in playlist');
            }
            
            if (!videos[0] || !videos[0].url) {
                throw new Error('First video has no URL: ' + JSON.stringify(videos[0]));
            }
            
            const resultsDiv = document.getElementById('resultsSection');
            if (!resultsDiv) {
                throw new Error('Results section not found');
            }
            
            // Ensure results section is visible
            resultsDiv.classList.remove('hidden');
            
            const playlistHtml = `
                <div class="playlist-container">
                    <h3>Video Playlist for: "${input}"</h3>
                    <div class="playlist-info">
                        <p>Videos will play one after another. ${videos.length} videos in sequence.</p>
                    </div>
                    <div class="playlist-player">
                        <video id="playlist-video" controls style="width: 100%; max-width: 600px;">
                            <source src="${videos[0].url}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                    <div class="playlist-controls">
                        <button onclick="fingerspellingApp.playPlaylist()">Play Playlist</button>
                        <button onclick="fingerspellingApp.pausePlaylist()">Pause</button>
                        <span id="playlist-status">Video 1 of ${videos.length}</span>
                    </div>
                </div>
            `;
            
            resultsDiv.innerHTML = playlistHtml;
            console.log('HTML set successfully');
            
            // Scroll to the results section
            resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
            this.setupPlaylistEvents(videos);
            console.log('Playlist events set up successfully');
            
        } catch (error) {
            console.error('Error displaying video playlist:', error);
            throw error; // Re-throw to be caught by the calling method
        }
    }
    
    // Set up playlist event handlers
    setupPlaylistEvents(videos) {
        console.log('Setting up playlist events for', videos.length, 'videos');
        
        this.currentPlaylist = videos;
        this.currentVideoIndex = 0;
        
        const video = document.getElementById('playlist-video');
        if (!video) {
            throw new Error('Playlist video element not found after setting HTML');
        }
        
        console.log('Video element found, adding event listeners');
        
        video.addEventListener('ended', () => {
            console.log('Video ended, playing next');
            this.playNextInPlaylist();
        });
        
        video.addEventListener('error', () => {
            console.error(`Error playing video ${this.currentVideoIndex + 1}`);
            this.playNextInPlaylist();
        });
        
        // Auto-play first video
        video.play().catch(e => console.log('Auto-play prevented by browser'));
        console.log('Playlist events setup complete');
    }
    
    // Play playlist from beginning
    playPlaylist() {
        if (!this.currentPlaylist || this.currentPlaylist.length === 0) {
            console.error('No playlist available');
            return;
        }
        
        this.currentVideoIndex = 0;
        this.loadCurrentVideo();
        
        const video = document.getElementById('playlist-video');
        video.play().catch(e => console.log('Auto-play prevented by browser'));
    }
    
    // Play next video in playlist
    playNextInPlaylist() {
        if (this.currentVideoIndex < this.currentPlaylist.length - 1) {
            this.currentVideoIndex++;
            this.loadCurrentVideo();
        } else {
            // Playlist finished
            document.getElementById('playlist-status').textContent = 'Playlist completed';
        }
    }
    
    // Load and play current video
    loadCurrentVideo() {
        const video = document.getElementById('playlist-video');
        const statusSpan = document.getElementById('playlist-status');
        
        video.src = this.currentPlaylist[this.currentVideoIndex].url;
        statusSpan.textContent = `Video ${this.currentVideoIndex + 1} of ${this.currentPlaylist.length}`;
        
        video.play().catch(e => console.log('Auto-play prevented by browser'));
    }
    
    // Pause playlist
    pausePlaylist() {
        const video = document.getElementById('playlist-video');
        video.pause();
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorState').classList.remove('hidden');
    }

    hideError() {
        document.getElementById('errorState').classList.add('hidden');
    }

    showResults() {
        document.getElementById('resultsSection').classList.remove('hidden');
        // Smooth scroll to results
        document.getElementById('resultsSection').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }

    hideResults() {
        document.getElementById('resultsSection').classList.add('hidden');
    }
}

// Animation utilities
class AnimationUtils {
    static fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = (timestamp - start) / duration;
            
            element.style.opacity = Math.min(progress, 1);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    static fadeOut(element, duration = 300) {
        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = (timestamp - start) / duration;
            
            element.style.opacity = Math.max(1 - progress, 0);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        };
        
        requestAnimationFrame(animate);
    }

    static slideDown(element, duration = 300) {
        element.style.maxHeight = '0px';
        element.style.overflow = 'hidden';
        element.style.display = 'block';
        
        const targetHeight = element.scrollHeight;
        let start = null;
        
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = (timestamp - start) / duration;
            
            element.style.maxHeight = (targetHeight * Math.min(progress, 1)) + 'px';
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.style.maxHeight = 'none';
                element.style.overflow = 'visible';
            }
        };
        
        requestAnimationFrame(animate);
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.fingerspellingApp = new FingerspellingApp();
    
    // Add some nice loading effects
    document.querySelectorAll('.btn-animate').forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter to convert
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            window.fingerspellingApp.convertWord();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-backdrop').forEach(modal => {
                if (!modal.classList.contains('hidden')) {
                    modal.classList.add('hidden');
                }
            });
        }
    });

    console.log('🎉 Sinhala Fingerspelling App initialized successfully!');
});