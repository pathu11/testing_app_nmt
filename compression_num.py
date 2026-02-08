import cv2
import numpy as np
import os
from pathlib import Path
import subprocess
import json

class VideoCompressor:
    def __init__(self, input_folder, output_folder, 
                 target_resolution=(224, 224), 
                 target_fps=15, 
                 target_duration=2.5,
                 crf=32,
                 preset='veryfast'):
        """
        Maximum compression video processor
        
        Args:
            input_folder: Path to input videos
            output_folder: Path to save processed videos
            target_resolution: Tuple (width, height) - smaller = more compression
            target_fps: Target frames per second - lower = more compression
            target_duration: Target duration in seconds
            crf: Compression quality (28-35 for max compression, 32 recommended)
            preset: Encoding speed (veryfast, faster, fast, medium)
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.target_resolution = target_resolution
        self.target_fps = target_fps
        self.target_duration = target_duration
        self.crf = crf
        self.preset = preset
        
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
    def estimate_output_size(self, width, height, fps, duration, crf):
        """Estimate output file size in MB"""
        pixels_per_frame = width * height
        
        # More aggressive compression factors
        if crf <= 23:
            bitrate_factor = 0.08
        elif crf <= 28:
            bitrate_factor = 0.04
        elif crf <= 32:
            bitrate_factor = 0.025
        else:
            bitrate_factor = 0.015
        
        estimated_bitrate = (pixels_per_frame / 1000) * bitrate_factor * fps
        file_size_mb = (estimated_bitrate * duration) / 8 / 1024
        
        return file_size_mb
    
    def get_video_info(self, video_path):
        """Get video metadata"""
        cap = cv2.VideoCapture(str(video_path))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        return {
            'width': width,
            'height': height,
            'fps': fps,
            'duration': duration,
            'frames': frame_count
        }
    
    def detect_motion_start(self, video_path, threshold=25, min_motion_frames=3):
        """
        Detect when significant motion starts - optimized version
        """
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Skip frames for faster processing
        skip_frames = max(1, int(fps / 10))  # Check ~10 frames per second
        
        ret, prev_frame = cap.read()
        if not ret:
            cap.release()
            return 0
        
        # Downsample for faster processing
        small_prev = cv2.resize(prev_frame, (160, 120))
        prev_gray = cv2.cvtColor(small_prev, cv2.COLOR_BGR2GRAY)
        prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)
        
        motion_counter = 0
        frame_count = 0
        motion_start_frame = 0
        
        while True:
            # Skip frames
            for _ in range(skip_frames):
                ret = cap.grab()
                if not ret:
                    break
            
            ret, frame = cap.retrieve()
            if not ret:
                break
            
            frame_count += skip_frames
            
            small_frame = cv2.resize(frame, (160, 120))
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            frame_diff = cv2.absdiff(prev_gray, gray)
            thresh = cv2.threshold(frame_diff, threshold, 255, cv2.THRESH_BINARY)[1]
            
            motion_pixels = np.count_nonzero(thresh)
            
            if motion_pixels > 500:  # Adjusted for smaller frame
                motion_counter += 1
                if motion_counter >= min_motion_frames:
                    motion_start_frame = max(0, frame_count - (min_motion_frames * skip_frames))
                    break
            else:
                motion_counter = 0
            
            prev_gray = gray
        
        cap.release()
        start_time = max(0, motion_start_frame / fps)
        return start_time
    
    def compress_with_ffmpeg(self, input_path, output_path, start_time=0):
        """
        Maximum compression using FFmpeg with H.265 (HEVC)
        """
        width, height = self.target_resolution
        
        # Try H.265 first (better compression), fallback to H.264
        commands = [
            # H.265 (HEVC) - Best compression
            [
                'ffmpeg', '-i', str(input_path),
                '-ss', str(start_time),
                '-t', str(self.target_duration),
                '-vf', f'scale={width}:{height}:flags=lanczos,fps={self.target_fps}',
                '-c:v', 'libx265',
                '-crf', str(self.crf),
                '-preset', self.preset,
                '-tag:v', 'hvc1',  # Better compatibility
                '-pix_fmt', 'yuv420p',
                '-an',  # No audio
                '-movflags', '+faststart',  # Web optimization
                '-y', str(output_path)
            ],
            # H.264 - Fallback if H.265 not available
            [
                'ffmpeg', '-i', str(input_path),
                '-ss', str(start_time),
                '-t', str(self.target_duration),
                '-vf', f'scale={width}:{height}:flags=lanczos,fps={self.target_fps}',
                '-c:v', 'libx264',
                '-crf', str(self.crf),
                '-preset', self.preset,
                '-pix_fmt', 'yuv420p',
                '-an',
                '-movflags', '+faststart',
                '-y', str(output_path)
            ]
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                return True
            except subprocess.CalledProcessError:
                continue
        
        return False
    
    def compress_with_opencv(self, input_path, output_path, start_time=0):
        """
        Fallback compression using OpenCV
        """
        cap = cv2.VideoCapture(str(input_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        start_frame = int(start_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        frames_to_process = int(self.target_duration * self.target_fps)
        
        # Use H264 codec with maximum compression
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(str(output_path), fourcc, self.target_fps, 
                             self.target_resolution)
        
        frame_count = 0
        skip_rate = max(1, int(fps / self.target_fps))
        last_frame = None
        
        while frame_count < frames_to_process:
            ret, frame = cap.read()
            if not ret:
                if last_frame is not None:
                    frame = last_frame
                else:
                    break
            
            # Skip frames for target FPS
            if frame_count % skip_rate == 0:
                resized = cv2.resize(frame, self.target_resolution, 
                                   interpolation=cv2.INTER_AREA)
                out.write(resized)
                last_frame = resized
            
            frame_count += 1
        
        cap.release()
        out.release()
        return True
    
    def analyze_and_estimate(self):
        """
        Analyze all videos and show size estimates before processing
        """
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        video_files = [f for f in self.input_folder.iterdir() 
                      if f.suffix.lower() in video_extensions]
        
        if not video_files:
            print("❌ No video files found!")
            return None
        
        print("\n" + "="*70)
        print("📊 VIDEO ANALYSIS & SIZE ESTIMATION")
        print("="*70)
        
        total_original_size = 0
        total_estimated_size = 0
        
        analysis_data = []
        
        for video_path in video_files:
            try:
                info = self.get_video_info(video_path)
                original_size_mb = video_path.stat().st_size / (1024 * 1024)
                
                estimated_size_mb = self.estimate_output_size(
                    self.target_resolution[0],
                    self.target_resolution[1],
                    self.target_fps,
                    self.target_duration,
                    self.crf
                )
                
                total_original_size += original_size_mb
                total_estimated_size += estimated_size_mb
                
                analysis_data.append({
                    'name': video_path.name,
                    'original_size': original_size_mb,
                    'estimated_size': estimated_size_mb,
                    'original_resolution': f"{info['width']}x{info['height']}",
                    'original_duration': info['duration']
                })
            except Exception as e:
                print(f"⚠️  Error analyzing {video_path.name}: {e}")
        
        # Display summary
        print(f"\n📁 Found: {len(video_files)} videos")
        print(f"📐 Target Resolution: {self.target_resolution[0]}x{self.target_resolution[1]}")
        print(f"🎬 Target FPS: {self.target_fps}")
        print(f"⏱️  Target Duration: {self.target_duration}s")
        print(f"🗜️  CRF: {self.crf} (higher = more compression)")
        
        print("\n" + "-"*70)
        print(f"{'VIDEO NAME':<35} {'ORIGINAL':<15} {'ESTIMATED':<15}")
        print("-"*70)
        
        for data in analysis_data[:10]:  # Show first 10
            print(f"{data['name'][:34]:<35} "
                  f"{data['original_size']:>6.2f} MB     "
                  f"{data['estimated_size']:>6.2f} MB")
        
        if len(analysis_data) > 10:
            print(f"... and {len(analysis_data) - 10} more videos")
        
        print("-"*70)
        print(f"{'TOTAL:':<35} {total_original_size:>6.2f} MB     "
              f"{total_estimated_size:>6.2f} MB")
        
        compression_ratio = ((total_original_size - total_estimated_size) / 
                           total_original_size * 100)
        
        print(f"\n💾 Total Original Size: {total_original_size:.2f} MB "
              f"({total_original_size/1024:.2f} GB)")
        print(f"📦 Total Estimated Size: {total_estimated_size:.2f} MB "
              f"({total_estimated_size/1024:.2f} GB)")
        print(f"🎯 Estimated Compression: {compression_ratio:.1f}% reduction")
        print(f"📉 Space Saved: ~{total_original_size - total_estimated_size:.2f} MB")
        
        return video_files, total_original_size, total_estimated_size
    
    def process_all_videos(self, auto_detect_start=True, use_ffmpeg=True):
        """
        Process all videos with progress tracking
        """
        # First, analyze and estimate
        result = self.analyze_and_estimate()
        if not result:
            return
        
        video_files, total_original, total_estimated = result
        
        print("\n" + "="*70)
        response = input("⚡ Start processing? (y/n): ").strip().lower()
        if response != 'y':
            print("❌ Processing cancelled")
            return
        
        print("\n" + "="*70)
        print("🚀 STARTING COMPRESSION")
        print("="*70 + "\n")
        
        total_actual_size = 0
        successful = 0
        failed = 0
        
        for i, video_path in enumerate(video_files, 1):
            print(f"\n[{i}/{len(video_files)}] 🎥 {video_path.name}")
            
            try:
                # Detect motion start
                start_time = 0
                if auto_detect_start:
                    print("  🔍 Detecting motion...", end=" ", flush=True)
                    start_time = self.detect_motion_start(video_path)
                    print(f"✓ (starts at {start_time:.2f}s)")
                
                # Output path
                output_path = self.output_folder / f"compressed_{video_path.stem}.mp4"
                
                # Compress
                print("  ⚙️  Compressing...", end=" ", flush=True)
                
                if use_ffmpeg:
                    success = self.compress_with_ffmpeg(video_path, output_path, start_time)
                else:
                    success = self.compress_with_opencv(video_path, output_path, start_time)
                
                if success and output_path.exists():
                    original_size = video_path.stat().st_size / (1024 * 1024)
                    compressed_size = output_path.stat().st_size / (1024 * 1024)
                    compression = ((original_size - compressed_size) / original_size * 100)
                    
                    total_actual_size += compressed_size
                    successful += 1
                    
                    print(f"✓")
                    print(f"  📊 {original_size:.2f} MB → {compressed_size:.2f} MB "
                          f"({compression:.1f}% smaller)")
                else:
                    failed += 1
                    print(f"✗ Failed")
                    
            except Exception as e:
                failed += 1
                print(f"  ❌ Error: {e}")
        
        # Final summary
        print("\n" + "="*70)
        print("✅ COMPRESSION COMPLETE")
        print("="*70)
        print(f"✓ Successful: {successful}/{len(video_files)}")
        print(f"✗ Failed: {failed}/{len(video_files)}")
        print(f"\n💾 Original Total: {total_original:.2f} MB")
        print(f"📦 Compressed Total: {total_actual_size:.2f} MB")
        print(f"🎯 Actual Compression: {((total_original - total_actual_size) / total_original * 100):.1f}%")
        print(f"💰 Space Saved: {total_original - total_actual_size:.2f} MB")
        print("="*70 + "\n")


# ============= PRESET CONFIGURATIONS =============

def max_compression_preset():
    """Ultra compression - smallest file size"""
    return {
        'target_resolution': (224, 224),
        'target_fps': 12,
        'target_duration': 2,
        'crf': 34,
        'preset': 'veryfast'
    }

def balanced_preset():
    """Balanced quality and size"""
    return {
        'target_resolution': (320, 240),
        'target_fps': 15,
        'target_duration': 2.5,
        'crf': 30,
        'preset': 'fast'
    }

def quality_preset():
    """Better quality, moderate compression"""
    return {
        'target_resolution': (480, 360),
        'target_fps': 20,
        'target_duration': 3,
        'crf': 28,
        'preset': 'medium'
    }

def mini_preset():
    """Extreme compression for thumbnails/preview"""
    return {
        'target_resolution': (160, 120),
        'target_fps': 10,
        'target_duration': 1.5,
        'crf': 35,
        'preset': 'veryfast'
    }


# ============= MAIN USAGE =============

if __name__ == "__main__":
    # Set your paths
    INPUT_FOLDER = "numbers"
    OUTPUT_FOLDER = "compressed_numbers"
    
    # Choose a preset or custom settings
    print("\n🎬 VIDEO COMPRESSOR")
    print("="*70)
    print("Select compression preset:")
    print("1. 🔥 MAX COMPRESSION (224x224, 12fps, ~100-150 KB per video)")
    print("2. ⚖️  BALANCED (320x240, 15fps, ~200-300 KB per video)")
    print("3. 📹 QUALITY (480x360, 20fps, ~400-600 KB per video)")
    print("4. 🔬 MINI (160x120, 10fps, ~50-80 KB per video)")
    print("5. ⚙️  CUSTOM")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    presets = {
        '1': max_compression_preset(),
        '2': balanced_preset(),
        '3': quality_preset(),
        '4': mini_preset()
    }
    
    if choice in presets:
        config = presets[choice]
    else:
        # Custom settings
        config = {
            'target_resolution': (224, 224),
            'target_fps': 15,
            'target_duration': 2.5,
            'crf': 32,
            'preset': 'veryfast'
        }
    
    # Initialize compressor
    compressor = VideoCompressor(
        input_folder=INPUT_FOLDER,
        output_folder=OUTPUT_FOLDER,
        **config
    )
    
    # Process all videos
    compressor.process_all_videos(
        auto_detect_start=True,  # Set False to disable motion detection
        use_ffmpeg=True          # Set False if FFmpeg not installed
    )


"""🔥 MAX COMPRESSION (224x224, 12fps, 2s):
   Per video: 100-150 KB
   1000 videos: ~100-150 MB
   Quality: Good for training/recognition

⚖️ BALANCED (320x240, 15fps, 2.5s):
   Per video: 200-300 KB
   1000 videos: ~200-300 MB
   Quality: Good balance

📹 QUALITY (480x360, 20fps, 3s):
   Per video: 400-600 KB
   1000 videos: ~400-600 MB
   Quality: Clear details

🔬 MINI (160x120, 10fps, 1.5s):
   Per video: 50-80 KB
   1000 videos: ~50-80 MB
   Quality: Minimal but recognizable
"""