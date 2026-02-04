"""
Main Fingerspelling Application
Combines all components for the web application
"""

from fingerspelling_converter import SinhalaFingerspellingConverter
from video_processor import VideoProcessor, VideoSequenceGenerator
from video_concatenator import VideoConcatenator, NumberConverter
import json


class FingerspellingApp:
    """
    Main application class that orchestrates the fingerspelling process
    """
    
    def __init__(self, videos_path="letters", mapping_file="fingerspelling_mapper.csv"):
        """
        Initialize the application
        
        Args:
            videos_path (str): Path to video files directory
            mapping_file (str): Path to the mapping CSV file
        """
        self.converter = SinhalaFingerspellingConverter()
        self.video_processor = VideoProcessor(videos_path, mapping_file)
        self.sequence_generator = VideoSequenceGenerator(self.video_processor)
        self.video_concatenator = VideoConcatenator()
        self.number_converter = NumberConverter()
    
    def process_word(self, word):
        """
        Complete processing of a word: convert to signs and get video sequence
        
        Args:
            word (str): Input Sinhala word
            
        Returns:
            dict: Complete processing result
        """
        result = {
            'input_word': word,
            'success': False,
            'error': None,
            'signs': [],
            'video_sequence': [],
            'sequence_info': {}
        }
        
        try:
            # Convert word to fingerspelling signs
            signs = self.converter.to_fingerspelling(word)
            result['signs'] = signs
            
            # Generate video sequence
            sequence_info = self.sequence_generator.generate_sequence(signs)
            result['sequence_info'] = sequence_info
            result['video_sequence'] = sequence_info['video_sequence']
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def process_multiple_words(self, words):
        """
        Process multiple words
        
        Args:
            words (list): List of Sinhala words
            
        Returns:
            list: List of processing results
        """
        results = []
        for word in words:
            results.append(self.process_word(word))
        return results
    
    def get_video_urls_for_word(self, word, base_url="/videos/"):
        """
        Get web-compatible video URLs for a word
        
        Args:
            word (str): Input Sinhala word
            base_url (str): Base URL for videos
            
        Returns:
            dict: Video URLs and metadata
        """
        result = {
            'input_word': word,
            'success': False,
            'signs': [],
            'video_urls': [],
            'error': None
        }
        
        try:
            # Convert to signs
            signs = self.converter.to_fingerspelling(word)
            result['signs'] = signs
            
            # Get video URLs
            video_urls = self.sequence_generator.get_video_urls_for_web(signs, base_url)
            result['video_urls'] = video_urls
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def process_word_with_concatenation(self, word):
        """
        Process word and create concatenated video
        
        Args:
            word (str): Input Sinhala word
            
        Returns:
            dict: Complete processing result with concatenated video
        """
        result = self.process_word(word)
        
        if result['success'] and result['video_sequence']:
            # Get actual video file paths
            video_paths = []
            for video_info in result['video_sequence']:
                if video_info['found'] and video_info['video_path']:
                    video_paths.append(video_info['video_path'])
                else:
                    video_paths.append(None)
            
            # Attempt video concatenation
            concat_result = self.video_concatenator.concatenate_videos(
                video_paths, word, result['signs']
            )
            
            result['concatenated_video'] = concat_result
        
        return result
    
    def process_number(self, number_input):
        """
        Process number input using mapper-based conversion and get video sequence
        
        Args:
            number_input (str or int): Number to process
            
        Returns:
            dict: Number processing result with video URLs
        """
        result = {
            'input_number': str(number_input),
            'success': False,
            'signs': [],
            'video_urls': [],
            'video_sequence': [],
            'sequence_info': {},
            'error': None
        }
        
        try:
            # Convert number to signs using mapper-based rules
            signs = self.number_converter.number_to_signs(number_input)
            result['signs'] = signs
            
            # Get video information for each sign
            video_info = self.number_converter.get_video_paths_for_number(number_input)
            result['video_urls'] = video_info
            
            # Generate video sequence for compatibility
            sequence_list = []
            for info in video_info:
                sequence_list.append({
                    'sign': info['sign'],
                    'video_path': info['video_path'],
                    'found': info['available'],
                    'url': info['url']
                })
            
            result['video_sequence'] = sequence_list
            result['sequence_info'] = {
                'total_signs': len(signs),
                'videos_found': sum(1 for info in video_info if info['available']),
                'videos_missing': sum(1 for info in video_info if not info['available']),
                'video_sequence': sequence_list
            }
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def process_number_with_concatenation(self, number_input):
        """
        Process number and create concatenated video using mapper-based conversion
        
        Args:
            number_input (str or int): Number to process
            
        Returns:
            dict: Complete number processing result with concatenated video
        """
        result = self.process_number(number_input)
        
        if result['success'] and result['video_sequence']:
            # Get actual video file paths from the number converter
            video_paths = []
            for video_info in result['video_sequence']:
                if video_info['found'] and video_info['video_path']:
                    video_paths.append(video_info['video_path'])
            
            # Create concatenated video if we have video paths
            if video_paths:
                try:
                    concatenation_result = self.video_concatenator.concatenate_videos(
                        video_paths, 
                        str(number_input), 
                        result['signs']
                    )
                    result['concatenated_video'] = concatenation_result
                except Exception as e:
                    result['concatenated_video'] = {
                        'success': False,
                        'error': f'Video concatenation failed: {str(e)}'
                    }
            else:
                result['concatenated_video'] = {
                    'success': False,
                    'error': 'No video files available for concatenation'
                }
        else:
            result['concatenated_video'] = {
                'success': False,
                'error': 'Number processing failed'
            }
            
        return result

    def get_app_statistics(self):
        """
        Get comprehensive application statistics
        
        Returns:
            dict: Application statistics
        """
        video_stats = self.video_processor.get_sign_statistics()
        available_signs = self.video_processor.get_available_signs()
        cache_info = self.video_concatenator.get_cache_info()
        available_numbers = self.number_converter.get_available_numbers()
        
        return {
            'video_statistics': video_stats,
            'available_signs_count': len(available_signs),
            'available_signs': available_signs,
            'converter_rules': {
                'total_allowed_signs': len(self.converter.rules.ALLOWED_SIGNS),
                'vowel_mappings': len(self.converter.rules.VOWEL_MAP)
            },
            'video_concatenation': cache_info,
            'number_support': {
                'available_numbers': len(available_numbers),
                'number_range': f"{min(available_numbers)}-{max(available_numbers)}"
            }
        }
    
    def validate_setup(self):
        """
        Validate the complete application setup
        
        Returns:
            dict: Validation results
        """
        validation_result = self.video_processor.validate_mappings()
        
        # Test conversion with sample words
        test_words = ["අමල", "කමල", "නමල"]  # Simple test words
        conversion_tests = []
        
        for word in test_words:
            try:
                signs = self.converter.to_fingerspelling(word)
                conversion_tests.append({
                    'word': word,
                    'signs': signs,
                    'success': True
                })
            except Exception as e:
                conversion_tests.append({
                    'word': word,
                    'error': str(e),
                    'success': False
                })
        
        return {
            'video_validation': validation_result,
            'conversion_tests': conversion_tests,
            'overall_status': validation_result['valid'] and all(test['success'] for test in conversion_tests)
        }


# Utility functions for the web application
def create_sample_data():
    """Create sample data for testing"""
    sample_names = [
        "අමල", "කමල", "නමල", "සුනිල්", "නිමල්",
        "ගම්පහ", "කොළඹ", "මාතර", "කණ්ඩි", "අනුරාධපුර"
    ]
    
    sample_villages = [
        "බණ්ඩාරවෙල", "හබරණ", "මීගමුව", "වරණ", "පානදුර"
    ]
    
    return {
        'names': sample_names,
        'villages': sample_villages,
        'all_samples': sample_names + sample_villages
    }

def export_app_data_for_web(app, output_file="app_data.json"):
    """
    Export all necessary data for the web application
    
    Args:
        app (FingerspellingApp): The main app instance
        output_file (str): Output JSON file path
    """
    # Get sample data
    samples = create_sample_data()
    
    # Process samples
    processed_samples = {}
    for category, words in samples.items():
        if category != 'all_samples':  # Skip the combined list
            processed_samples[category] = []
            for word in words:
                result = app.get_video_urls_for_word(word)
                processed_samples[category].append(result)
    
    # Create comprehensive export
    export_data = {
        'app_statistics': app.get_app_statistics(),
        'sample_data': samples,
        'processed_samples': processed_samples,
        'validation': app.validate_setup()
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"App data exported to {output_file}")