"""
Flask Web Application for Sinhala Fingerspelling
Modern, responsive web interface for fingerspelling visualization
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from fingerspelling_app import FingerspellingApp
import os
import json
from pathlib import Path


app = Flask(__name__)

# Initialize the fingerspelling application
fingerspelling_app = FingerspellingApp()

# Configuration
app.config['VIDEOS_FOLDER'] = 'compressed_letters'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')


@app.route('/test')
def test():
    """Simple test page"""
    return render_template('test.html')


@app.route('/api/convert', methods=['POST'])
def convert_text():
    """
    API endpoint to convert Sinhala text to fingerspelling
    
    Expected JSON: {"text": "සිංහල වචනය"}
    Returns: Complete processing result
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Text field is required'
            }), 400
        
        text = data['text'].strip()
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Text cannot be empty'
            }), 400
        
        # Process the word
        result = fingerspelling_app.process_word(text)
        
        # Get video URLs for web player
        if result['success']:
            video_urls_result = fingerspelling_app.get_video_urls_for_word(text, '/videos/')
            result.update(video_urls_result)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/convert-number', methods=['POST'])
def convert_number():
    """
    API endpoint to convert numbers to fingerspelling
    
    Expected JSON: {"number": "123"}
    Returns: Complete processing result
    """
    try:
        data = request.get_json()
        
        if not data or 'number' not in data:
            return jsonify({
                'success': False,
                'error': 'Number field is required'
            }), 400
        
        number_input = data['number']
        
        if not str(number_input).strip():
            return jsonify({
                'success': False,
                'error': 'Number cannot be empty'
            }), 400
        
        # Process the number
        result = fingerspelling_app.process_number(number_input)
        
        # Get video URLs for web player if successful
        if result['success']:
            video_urls = []
            for sign in result['signs']:
                video_path = fingerspelling_app.video_processor.get_video_for_sign(sign)
                if video_path:
                    video_filename = Path(video_path).name
                    video_urls.append({
                        'sign': sign,
                        'url': '/videos/' + video_filename,
                        'filename': video_filename
                    })
                else:
                    video_urls.append({
                        'sign': sign,
                        'url': None,
                        'filename': None,
                        'error': 'Video not found'
                    })
            
            result['video_urls'] = video_urls
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
def batch_convert_text():
    """
    API endpoint to convert multiple words
    
    Expected JSON: {"words": ["වචනය1", "වචනය2"]}
    """
    try:
        data = request.get_json()
        
        if not data or 'words' not in data:
            return jsonify({
                'success': False,
                'error': 'Words array is required'
            }), 400
        
        words = [word.strip() for word in data['words'] if word.strip()]
        
        if not words:
            return jsonify({
                'success': False,
                'error': 'At least one valid word is required'
            }), 400
        
        results = fingerspelling_app.process_multiple_words(words)
        
        return jsonify({
            'success': True,
            'results': results,
            'total_words': len(words)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/statistics')
def get_statistics():
    """Get application statistics"""
    try:
        stats = fingerspelling_app.get_app_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting statistics: {str(e)}'
        }), 500


@app.route('/api/concatenate-video', methods=['POST'])
def concatenate_video():
    """
    API endpoint to create concatenated video for text/number
    
    Expected JSON: {"text": "වචනය", "type": "text"} or {"number": "123", "type": "number"}
    Returns: Concatenated video information
    """
    try:
        data = request.get_json()
        
        if not data or 'type' not in data:
            return jsonify({
                'success': False,
                'error': 'Type field is required (text or number)'
            }), 400
        
        input_type = data['type']
        
        if input_type == 'text':
            if 'text' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Text field is required for text type'
                }), 400
            
            text = data['text'].strip()
            if not text:
                return jsonify({
                    'success': False,
                    'error': 'Text cannot be empty'
                }), 400
                
            result = fingerspelling_app.process_word_with_concatenation(text)
            
        elif input_type == 'number':
            if 'number' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Number field is required for number type'
                }), 400
            
            number = data['number']
            if not str(number).strip():
                return jsonify({
                    'success': False,
                    'error': 'Number cannot be empty'
                }), 400
                
            result = fingerspelling_app.process_number_with_concatenation(number)
            
        else:
            return jsonify({
                'success': False,
                'error': 'Type must be "text" or "number"'
            }), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
def validate_setup():
    """Validate application setup"""
    try:
        validation = fingerspelling_app.validate_setup()
        return jsonify({
            'success': True,
            'validation': validation
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Validation error: {str(e)}'
        }), 500


@app.route('/concatenated-videos/<filename>')
def serve_concatenated_video(filename):
    """Serve concatenated video files (keep until new one is generated)"""
    try:
        temp_dir = fingerspelling_app.video_concatenator.temp_dir
        return send_from_directory(temp_dir, filename)
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Concatenated video file not found'
        }), 404
@app.route('/videos/<filename>')
def serve_video(filename):
    """Serve video files"""
    try:
        return send_from_directory(app.config['VIDEOS_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Video file not found'
        }), 404


@app.route('/api/video-playlist', methods=['POST'])
def create_video_playlist():
    """Create a video playlist for sequential playback when concatenation fails"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        input_type = data.get('type', 'text')
        
        if input_type == 'text':
            if 'text' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Text field is required'
                }), 400
                
            result = fingerspelling_app.process_word(data['text'])
            
        elif input_type == 'number':
            if 'number' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Number field is required'
                }), 400
                
            result = fingerspelling_app.process_number(data['number'])
            
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid type. Must be "text" or "number"'
            }), 400
        
        if not result['success']:
            return jsonify(result), 400
            
        # Generate video URLs for playlist
        video_urls = []
        for sign in result['signs']:
            video_path = fingerspelling_app.video_processor.get_video_for_sign(sign)
            if video_path:
                video_filename = Path(video_path).name
                video_urls.append({
                    'sign': sign,
                    'url': '/videos/' + video_filename,
                    'filename': video_filename
                })
            else:
                video_urls.append({
                    'sign': sign,
                    'url': None,
                    'filename': None,
                    'error': 'Video not found'
                })
        
        # Create playlist data
        playlist = {
            'success': True,
            'type': 'playlist',
            'input': data.get('text', data.get('number')),
            'signs': result.get('signs', []),
            'videos': video_urls,
            'playback_mode': 'sequential',
            'note': 'Videos will play one after another automatically'
        }
        
        return jsonify(playlist)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status')
def get_status():
    """Get application status including MoviePy availability"""
    try:
        moviepy_status = fingerspelling_app.video_concatenator.get_moviepy_status()
        
        return jsonify({
            'success': True,
            'moviepy': moviepy_status,
            'video_mappings': {
                'total': 121,
                'found': 120,
                'missing': 1
            },
            'features': {
                'text_conversion': True,
                'number_conversion': True,
                'video_playback': True,
                'video_concatenation': moviepy_status['available']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/samples')
def get_samples():
    """Get sample words for testing"""
    from fingerspelling_app import create_sample_data
    
    try:
        samples = create_sample_data()
        return jsonify({
            'success': True,
            'samples': samples
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error loading samples: {str(e)}'
        }), 500


@app.route('/api/cache-info')
def get_cache_info():
    """Get video cache information"""
    try:
        cache_info = fingerspelling_app.video_concatenator.get_cache_info()
        return jsonify({
            'success': True,
            'cache_info': cache_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting cache info: {str(e)}'
        }), 500


@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """Clear video cache"""
    try:
        result = fingerspelling_app.video_concatenator.clear_cache()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error clearing cache: {str(e)}'
        }), 500


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/demo')
def demo():
    """Demo page with examples"""
    return render_template('demo.html')


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


@app.route('/api/cleanup-temp-videos', methods=['POST'])
def cleanup_temp_videos():
    """Clean up old temporary concatenated videos (keeps most recent)"""
    try:
        # Clean up videos older than 24 hours (fallback cleanup)
        result = fingerspelling_app.video_concatenator.cleanup_temp_videos(max_age_hours=24)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Cleanup failed: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Clean up very old temporary videos on startup (keep recent ones)
    try:
        cleanup_result = fingerspelling_app.video_concatenator.cleanup_temp_videos(max_age_hours=24)
        if cleanup_result['success']:
            print(f"✅ Cleaned up {cleanup_result['cleaned_count']} very old temporary videos on startup")
    except Exception as e:
        print(f"Warning: Initial cleanup failed: {e}")
    
    # Validate setup on startup
    try:
        validation = fingerspelling_app.validate_setup()
        print("=== Application Setup Validation ===")
        print(f"Overall Status: {'✅ PASSED' if validation['overall_status'] else '❌ FAILED'}")
        print(f"Video Mappings: {validation['video_validation']['found_count']}/{validation['video_validation']['total_mappings']} found")
        
        if validation['video_validation']['missing_videos']:
            print("Missing videos:")
            for missing in validation['video_validation']['missing_videos'][:5]:  # Show first 5
                print(f"  - {missing['sign']}: {missing['video_file']}")
            if len(validation['video_validation']['missing_videos']) > 5:
                print(f"  ... and {len(validation['video_validation']['missing_videos']) - 5} more")
        
        print("=== Starting Flask Application ===")
        
    except Exception as e:
        print(f"Warning: Setup validation failed: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)