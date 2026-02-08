"""
Video Processing Manager for Fingerspelling Application
Handles video mapping, processing, and concatenation
"""

import pandas as pd
import os
from pathlib import Path
import json


class VideoProcessor:
    """
    Manages video files and their mapping to Sinhala signs
    """

    def __init__(self, videos_path, mapping_file):
        """
        Initialize the video processor
        
        Args:
            videos_path (str): Path to the directory containing video files
            mapping_file (str): Path to the CSV mapping file
        """
        self.videos_path = Path(videos_path)
        self.mapping_file = Path(mapping_file)
        self.sign_to_video = {}
        self.video_to_sign = {}
        self._load_mappings()

    def _load_mappings(self):
        """Load video to sign mappings from CSV file"""
        try:
            # Load the mapping file
            df = pd.read_csv(self.mapping_file, header=None, names=['video_file', 'sign'])
            
            # Create bidirectional mappings
            for _, row in df.iterrows():
                video_file = row['video_file']
                sign = str(row['sign'])  # Convert to string to handle both letters and numbers
                
                # Map sign to video file (add compressed_ prefix and .mp4 extension)
                video_file = 'compressed_' + video_file + '.mp4'
                
                self.sign_to_video[sign] = video_file
                self.video_to_sign[video_file] = sign
                
        except Exception as e:
            raise Exception(f"Error loading mappings from {self.mapping_file}: {str(e)}")

    def get_video_for_sign(self, sign):
        """
        Get the video file path for a given sign
        
        Args:
            sign (str): The Sinhala sign
            
        Returns:
            str: Full path to the video file, or None if not found
        """
        video_filename = self.sign_to_video.get(sign)
        if video_filename:
            video_path = self.videos_path / video_filename
            if video_path.exists():
                return str(video_path)
            else:
                print(f"Warning: Video file {video_filename} not found for sign '{sign}'")
                return None
        else:
            print(f"Warning: No video mapping found for sign '{sign}'")
            return None

    def get_videos_for_signs(self, signs):
        """
        Get video file paths for a list of signs
        
        Args:
            signs (list): List of Sinhala signs
            
        Returns:
            list: List of dictionaries with sign and video_path
        """
        result = []
        for sign in signs:
            video_path = self.get_video_for_sign(sign)
            result.append({
                'sign': sign,
                'video_path': video_path,
                'found': video_path is not None
            })
        return result

    def get_available_signs(self):
        """
        Get all available signs that have video mappings
        
        Returns:
            list: List of available signs
        """
        return list(self.sign_to_video.keys())

    def get_sign_statistics(self):
        """
        Get statistics about the video mappings
        
        Returns:
            dict: Statistics about mappings
        """
        total_mappings = len(self.sign_to_video)
        existing_videos = 0
        missing_videos = 0
        
        for video_filename in self.sign_to_video.values():
            video_path = self.videos_path / video_filename
            if video_path.exists():
                existing_videos += 1
            else:
                missing_videos += 1
        
        return {
            'total_mappings': total_mappings,
            'existing_videos': existing_videos,
            'missing_videos': missing_videos,
            'coverage_percentage': (existing_videos / total_mappings * 100) if total_mappings > 0 else 0
        }

    def validate_mappings(self):
        """
        Validate that all mapped videos exist
        
        Returns:
            dict: Validation results
        """
        missing_videos = []
        existing_videos = []
        
        for sign, video_filename in self.sign_to_video.items():
            video_path = self.videos_path / video_filename
            if video_path.exists():
                existing_videos.append({
                    'sign': sign,
                    'video_file': video_filename,
                    'path': str(video_path)
                })
            else:
                missing_videos.append({
                    'sign': sign,
                    'video_file': video_filename,
                    'expected_path': str(video_path)
                })
        
        return {
            'valid': len(missing_videos) == 0,
            'existing_videos': existing_videos,
            'missing_videos': missing_videos,
            'total_mappings': len(self.sign_to_video),
            'found_count': len(existing_videos),
            'missing_count': len(missing_videos)
        }

    def export_mappings_json(self, output_file):
        """
        Export mappings to JSON file for web application
        
        Args:
            output_file (str): Path to output JSON file
        """
        mappings_data = {
            'sign_to_video': self.sign_to_video,
            'video_to_sign': self.video_to_sign,
            'videos_path': str(self.videos_path),
            'statistics': self.get_sign_statistics()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mappings_data, f, ensure_ascii=False, indent=2)

class VideoSequenceGenerator:
    """
    Generates video sequences for fingerspelling words
    """
    
    def __init__(self, video_processor):
        """
        Initialize with a video processor
        
        Args:
            video_processor (VideoProcessor): Instance of VideoProcessor
        """
        self.video_processor = video_processor
    
    def generate_sequence(self, signs):
        """
        Generate a video sequence for a list of signs
        
        Args:
            signs (list): List of Sinhala signs
            
        Returns:
            dict: Information about the video sequence
        """
        sequence_info = {
            'signs': signs,
            'video_sequence': [],
            'missing_signs': [],
            'total_signs': len(signs),
            'found_videos': 0,
            'missing_videos': 0
        }
        
        for sign in signs:
            video_data = self.video_processor.get_videos_for_signs([sign])[0]
            sequence_info['video_sequence'].append(video_data)
            
            if video_data['found']:
                sequence_info['found_videos'] += 1
            else:
                sequence_info['missing_videos'] += 1
                sequence_info['missing_signs'].append(sign)
        
        sequence_info['completion_percentage'] = (
            sequence_info['found_videos'] / sequence_info['total_signs'] * 100
            if sequence_info['total_signs'] > 0 else 0
        )
        
        return sequence_info
    
    def get_video_urls_for_web(self, signs, base_url="/videos/"):
        """
        Generate web-compatible video URLs for signs
        
        Args:
            signs (list): List of Sinhala signs
            base_url (str): Base URL for videos in web application
            
        Returns:
            list: List of video URLs for web player
        """
        video_urls = []
        for sign in signs:
            video_path = self.video_processor.get_video_for_sign(sign)
            if video_path:
                video_filename = Path(video_path).name
                video_urls.append({
                    'sign': sign,
                    'url': base_url + video_filename,
                    'filename': video_filename
                })
            else:
                video_urls.append({
                    'sign': sign,
                    'url': None,
                    'filename': None,
                    'error': 'Video not found'
                })
        return video_urls