"""
Video Concatenation Module for Fingerspelling Application
Handles concatenating individual sign videos into complete word videos
"""

import os
import tempfile
import shutil
from pathlib import Path
import hashlib
import json
from datetime import datetime
import subprocess
import concurrent.futures

# Try to import MoviePy with more detailed error handling
try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
    MOVIEPY_ERROR = None
except ImportError as e:
    MOVIEPY_AVAILABLE = False
    MOVIEPY_ERROR = str(e)
except Exception as e:
    MOVIEPY_AVAILABLE = False
    MOVIEPY_ERROR = f"MoviePy import error: {str(e)}"


class VideoConcatenator:
    """
    Handles video concatenation for fingerspelling sequences
    """
    
    def __init__(self, temp_dir="temp_videos"):
        """
        Initialize the video concatenator for temporary storage only
        
        Args:
            temp_dir (str): Directory to store temporary concatenated videos
        """
        # Use /tmp for serverless environments, otherwise use the specified temp_dir
        import os
        if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            self.temp_dir = Path("/tmp") / "temp_videos"
        else:
            self.temp_dir = Path(temp_dir)
        # Don't create directory here - create when needed
        # self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize cache (disabled for serverless)
        self.cache_file = self.temp_dir / "cache.json"
        self.cache_data = {}
        self.max_cache_size = 0  # Disable caching for serverless
    
    def _ensure_temp_dir(self):
        """Ensure the temporary directory exists"""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def _cleanup_old_temp_videos(self, keep_recent=1):
        """
        Clean up old temporary videos, keeping the most recent ones
        
        Args:
            keep_recent (int): Number of most recent videos to keep
        """
        try:
            # Get all temp video files
            temp_files = list(self.temp_dir.glob("temp_*.mp4"))
            
            if len(temp_files) <= keep_recent:
                return  # Nothing to clean
                
            # Sort by modification time (newest first)
            temp_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep the most recent ones, delete the rest
            files_to_delete = temp_files[keep_recent:]
            cleaned_count = 0
            
            for video_file in files_to_delete:
                try:
                    video_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    print(f"Failed to delete {video_file}: {e}")
            
            if cleaned_count > 0:
                print(f"Cleaned up {cleaned_count} old temporary videos")
                
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def cleanup_temp_videos(self, max_age_hours=1):
        """
        Clean up temporary videos older than specified hours (legacy method)
        
        Args:
            max_age_hours (int): Maximum age of videos to keep in hours
        """
        import time
        
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_count = 0
            for video_file in self.temp_dir.glob("temp_*.mp4"):
                if video_file.is_file():
                    file_age = current_time - video_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        video_file.unlink()
                        cleaned_count += 1
            
            return {
                'success': True,
                'cleaned_count': cleaned_count,
                'message': f'Cleaned up {cleaned_count} temporary videos older than {max_age_hours} hours'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Cleanup failed: {str(e)}'
            }
        
    def _load_cache(self):
        """Load cache metadata"""
        if self.max_cache_size > 0 and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache metadata"""
        if self.max_cache_size > 0:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
    
    def _fast_concatenate_with_ffmpeg(self, video_paths, output_path):
        """
        Fast concatenation using FFmpeg concat demuxer (no re-encoding)
        Only works if all videos have same codec, resolution, etc.
        """
        try:
            # Create a temporary concat file
            concat_file = output_path.with_suffix('.txt')
            with open(concat_file, 'w') as f:
                for video_path in video_paths:
                    f.write(f"file '{video_path}'\n")

            # Run FFmpeg concat
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',  # No re-encoding
                '-y',  # Overwrite output
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Clean up concat file
            concat_file.unlink(missing_ok=True)

            if result.returncode == 0:
                return True
            else:
                print(f"FFmpeg concat failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"FFmpeg concatenation error: {e}")
            return False

    def _check_videos_compatible(self, video_paths):
        """
        Check if videos are compatible for fast concatenation
        """
        try:
            # Get video info for first video
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', video_paths[0]]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return False

            import json
            info = json.loads(result.stdout)
            video_stream = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)

            if not video_stream:
                return False

            reference_codec = video_stream.get('codec_name')
            reference_width = video_stream.get('width')
            reference_height = video_stream.get('height')

            # Check other videos
            for video_path in video_paths[1:]:
                cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', video_path]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    return False

                info = json.loads(result.stdout)
                video_stream = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)

                if not video_stream:
                    return False

                if (video_stream.get('codec_name') != reference_codec or
                    video_stream.get('width') != reference_width or
                    video_stream.get('height') != reference_height):
                    return False

            return True

        except Exception as e:
            print(f"Compatibility check error: {e}")
            return False
    
    def _get_video_hash(self, video_paths, word):
        """Generate a hash for the video sequence"""
        content = f"{word}:{':'.join(video_paths)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _cleanup_old_videos(self):
        """Remove old videos if cache size exceeds limit"""
        if len(self.cache_data) <= self.max_cache_size:
            return
            
        # Sort by last accessed time and remove oldest
        sorted_cache = sorted(
            self.cache_data.items(),
            key=lambda x: x[1].get('last_accessed', 0)
        )
        
        videos_to_remove = sorted_cache[:-self.max_cache_size]
        
        for video_hash, info in videos_to_remove:
            video_path = self.temp_dir / f"{video_hash}.mp4"
            if video_path.exists():
                video_path.unlink()
            del self.cache_data[video_hash]
        
        self._save_cache()
    
    def get_moviepy_status(self):
        """Get detailed MoviePy availability status"""
        return {
            'available': MOVIEPY_AVAILABLE,
            'error': MOVIEPY_ERROR if not MOVIEPY_AVAILABLE else None,
            'can_concatenate': MOVIEPY_AVAILABLE
        }
    
    def concatenate_videos(self, video_paths, word, signs):
        """
        Concatenate videos into a single temporary file (cleanup old ones when new one is created)
        
        Args:
            video_paths (list): List of video file paths
            word (str): The word being spelled
            signs (list): List of signs for the word
            
        Returns:
            dict: Result with temporary video path
        """
        if not MOVIEPY_AVAILABLE:
            error_msg = "MoviePy not available for video concatenation."
            if MOVIEPY_ERROR:
                error_msg += f" Error: {MOVIEPY_ERROR}"
            error_msg += " You can still view individual videos."
            
            return {
                'success': False,
                'error': error_msg,
                'fallback': 'individual_videos',
                'note': 'Individual video playback will still work'
            }
        
        # Filter out None/missing video paths
        valid_video_paths = [path for path in video_paths if path and os.path.exists(path)]
        
        if not valid_video_paths:
            return {
                'success': False,
                'error': 'No valid video files found',
                'missing_count': len(video_paths) - len(valid_video_paths)
            }
        
        # Clean up old temporary videos before creating new one (keep only the most recent)
        self._cleanup_old_temp_videos(keep_recent=1)
        
        # Ensure temp directory exists
        self._ensure_temp_dir()
        
        # Generate unique temporary filename
        import uuid
        temp_filename = f"temp_{uuid.uuid4().hex}.mp4"
        output_path = self.temp_dir / temp_filename
        
        # Try fast FFmpeg concatenation first (no re-encoding)
        if len(valid_video_paths) > 1 and self._check_videos_compatible(valid_video_paths):
            print(f"Using fast FFmpeg concatenation for {len(valid_video_paths)} compatible videos")
            if self._fast_concatenate_with_ffmpeg(valid_video_paths, output_path):
                return {
                    'success': True,
                    'video_path': str(output_path),
                    'cached': False,
                    'temporary': True,
                    'word': word,
                    'signs': signs,
                    'video_count': len(valid_video_paths),
                    'missing_count': len(video_paths) - len(valid_video_paths),
                    'method': 'ffmpeg_fast'
                }

        # Fall back to MoviePy concatenation
        print(f"Using MoviePy concatenation for {len(valid_video_paths)} videos")
        
        try:
            # Load video clips with optimizations
            clips = []
            failed_clips = []

            for i, video_path in enumerate(valid_video_paths):
                try:
                    # Load clip with audio disabled for faster processing (if no audio needed)
                    clip = VideoFileClip(video_path, audio=False)  # Skip audio for faster processing

                    # Only resize if height differs significantly (>100px difference)
                    if hasattr(clip, 'h') and abs(clip.h - 480) > 100:
                        clip = clip.resize(height=480)

                    clips.append(clip)
                except Exception as e:
                    failed_clips.append({'path': video_path, 'error': str(e), 'sign': signs[i] if i < len(signs) else 'unknown'})
                    continue

            if not clips:
                return {
                    'success': False,
                    'error': 'No video clips could be loaded',
                    'failed_clips': failed_clips
                }

            # Concatenate clips
            final_clip = concatenate_videoclips(clips, method="compose")

            # Write with optimized settings for speed
            final_clip.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                preset='fast',  # Faster encoding preset
                bitrate='800k',  # Lower bitrate for faster processing
                fps=24,  # Standard frame rate
                threads=2  # Use multiple threads
            )
            
            # Clean up clips to free memory
            for clip in clips:
                clip.close()
            final_clip.close()
            
            return {
                'success': True,
                'video_path': str(output_path),
                'cached': False,
                'temporary': True,
                'word': word,
                'signs': signs,
                'video_count': len(clips),
                'missing_count': len(video_paths) - len(valid_video_paths),
                'failed_clips': failed_clips,
                'method': 'moviepy'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Video concatenation failed: {str(e)}',
                'word': word
            }
    
    def get_cached_video(self, word, signs):
        """
        Get cached video for a word if it exists
        
        Args:
            word (str): The word
            signs (list): List of signs
            
        Returns:
            str or None: Path to cached video or None if not found
        """
        # This is a simplified check - in practice you'd want to match the exact sequence
        for video_hash, info in self.cache_data.items():
            if info.get('word') == word and info.get('signs') == signs:
                video_path = self.temp_dir / f"{video_hash}.mp4"
                if video_path.exists():
                    # Update access time
                    self.cache_data[video_hash]['last_accessed'] = datetime.now().timestamp()
                    self._save_cache()
                    return str(video_path)
        return None
    
    def clear_cache(self):
        """Clear all cached videos"""
        for video_file in self.temp_dir.glob("*.mp4"):
            video_file.unlink()
        
        self.cache_data = {}
        self._save_cache()
        
        return {"success": True, "message": "Cache cleared"}
    
    def get_cache_info(self):
        """Get information about cached videos"""
        total_size = 0
        video_count = 0
        
        for video_file in self.temp_dir.glob("*.mp4"):
            total_size += video_file.stat().st_size
            video_count += 1
        
        return {
            'video_count': video_count,
            'total_size_mb': total_size / (1024 * 1024),
            'cache_entries': len(self.cache_data),
            'temp_dir': str(self.temp_dir),
            'moviepy_available': MOVIEPY_AVAILABLE
        }


class NumberConverter:
    """
    Converts numbers to fingerspelling signs using mapper CSV file and hierarchical rules
    """
    
    def __init__(self, mapper_file='fingerspelling_mapper.csv', numbers_dir='letters'):
        self.mapper_file = mapper_file
        self.numbers_dir = numbers_dir
        self.number_mapping = self._load_number_mapping()
        
    def _load_number_mapping(self):
        """
        Load number to video mapping from CSV file
        """
        mapping = {}
        csv_path = Path(self.mapper_file)
        
        if not csv_path.exists():
            print(f"Warning: Mapper file {self.mapper_file} not found")
            return mapping
            
        try:
            import pandas as pd
            df = pd.read_csv(csv_path, header=None, names=['video_id', 'sign'])
            
            # Filter only numeric signs
            numeric_df = df[df['sign'].astype(str).str.isdigit()]
            
            for _, row in numeric_df.iterrows():
                try:
                    number = int(row['sign'])
                    video_id = row['video_id']
                    mapping[number] = {
                        'video_id': video_id,
                        'video_path': os.path.join(self.numbers_dir, f"{video_id}.MOV")
                    }
                except (ValueError, TypeError):
                    continue
                    
            print(f"✅ Loaded {len(mapping)} number mappings from CSV")
            
        except Exception as e:
            print(f"Warning: Error loading number mapping: {e}")
            
        return mapping
    
    def _get_number_components(self, number):
        """
        Decompose a number into components that exist in the mapping
        
        Examples:
        - 23: direct mapping exists -> [23]
        - 78: no direct mapping -> [70, 8]
        - 234: no direct mapping -> [200, 30, 4]
        - 1234: -> [1000, 200, 30, 4]
        """
        # First check if direct mapping exists
        if number in self.number_mapping:
            return [number]
            
        components = []
        remaining = number
        
        # Handle different number ranges
        if remaining >= 100000:
            # Hundred thousands
            hundreds_k = (remaining // 100000) * 100000
            if hundreds_k in self.number_mapping:
                components.append(hundreds_k)
                remaining -= hundreds_k
            else:
                # Break down further if needed
                hundreds_k_digit = remaining // 100000
                if hundreds_k_digit * 100000 in self.number_mapping:
                    components.append(hundreds_k_digit * 100000)
                    remaining -= hundreds_k_digit * 100000
                    
        if remaining >= 10000:
            # Ten thousands  
            tens_k = (remaining // 10000) * 10000
            if tens_k in self.number_mapping:
                components.append(tens_k)
                remaining -= tens_k
            else:
                # Try individual ten thousands
                tens_k_digit = remaining // 10000
                if 10000 in self.number_mapping:
                    for _ in range(tens_k_digit):
                        components.append(10000)
                    remaining -= tens_k_digit * 10000
                    
        if remaining >= 1000:
            # Thousands
            thousands = (remaining // 1000) * 1000
            if thousands in self.number_mapping:
                components.append(thousands)
                remaining -= thousands
            else:
                # Try 1000 base
                thousands_digit = remaining // 1000
                if 1000 in self.number_mapping:
                    for _ in range(thousands_digit):
                        components.append(1000)
                    remaining -= thousands_digit * 1000
                    
        if remaining >= 100:
            # Hundreds
            hundreds = (remaining // 100) * 100
            if hundreds in self.number_mapping:
                components.append(hundreds)
                remaining -= hundreds
            else:
                # Try 100 base  
                hundreds_digit = remaining // 100
                if 100 in self.number_mapping:
                    for _ in range(hundreds_digit):
                        components.append(100)
                    remaining -= hundreds_digit * 100
                    
        if remaining >= 10:
            # Tens
            tens = (remaining // 10) * 10
            if tens in self.number_mapping:
                components.append(tens)
                remaining -= tens
            else:
                # Break down to individual digits
                tens_digit = remaining // 10
                if tens_digit in self.number_mapping:
                    components.append(tens_digit)
                remaining = remaining % 10
                    
        if remaining > 0:
            # Units
            if remaining in self.number_mapping:
                components.append(remaining)
            else:
                # Fallback to individual digits if no mapping exists
                for digit_char in str(remaining):
                    digit = int(digit_char)
                    if digit in self.number_mapping:
                        components.append(digit)
                        
        return components if components else [number]  # Fallback to original number
    
    def number_to_signs(self, number_input):
        """
        Convert number input to fingerspelling signs using mapper-based rules
        
        Args:
            number_input (str or int): Number to convert
            
        Returns:
            list: List of signs for the number
        """
        try:
            # Handle string input
            if isinstance(number_input, str):
                number_input = number_input.strip()
                
            # Convert to integer
            if isinstance(number_input, str) and number_input.isdigit():
                number = int(number_input)
            elif isinstance(number_input, int):
                number = number_input
            else:
                # Fallback: individual digits
                return [char for char in str(number_input) if char.isdigit()]
                
            # Get number components using hierarchical rules
            components = self._get_number_components(number)
            
            # Convert components to signs
            signs = []
            for component in components:
                if component in self.number_mapping:
                    # Use the mapped number directly
                    signs.append(str(component))
                else:
                    # Fallback to individual digits
                    signs.extend([char for char in str(component)])
                    
            return signs
            
        except Exception as e:
            print(f"Error converting number {number_input}: {e}")
            # Fallback: return individual digits
            return [char for char in str(number_input) if char.isdigit()]
    
    def get_video_paths_for_number(self, number_input):
        """
        Get video paths for a number using the mapping
        
        Args:
            number_input (str or int): Number to get videos for
            
        Returns:
            list: List of dictionaries with sign and video path info
        """
        signs = self.number_to_signs(number_input)
        video_info = []
        
        for sign in signs:
            try:
                sign_num = int(sign)
                if sign_num in self.number_mapping:
                    mapping = self.number_mapping[sign_num]
                    video_path = mapping['video_path']
                    
                    video_info.append({
                        'sign': sign,
                        'video_path': video_path if os.path.exists(video_path) else None,
                        'url': f'/videos/{mapping["video_id"]}.MOV' if os.path.exists(video_path) else None,
                        'available': os.path.exists(video_path)
                    })
                else:
                    # No mapping available
                    video_info.append({
                        'sign': sign,
                        'video_path': None,
                        'url': None,
                        'available': False
                    })
            except (ValueError, TypeError):
                video_info.append({
                    'sign': sign,
                    'video_path': None,
                    'url': None,
                    'available': False
                })
                
        return video_info
    
    def get_available_numbers(self):
        """
        Get list of all numbers that have direct video mappings
        
        Returns:
            list: Sorted list of available numbers
        """
        return sorted(self.number_mapping.keys())