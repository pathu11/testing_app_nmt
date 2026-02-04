# Sinhala Fingerspelling Web Application

A modern, interactive web application for converting Sinhala text into fingerspelling sign language videos. Built with clean, modular Python code and a beautiful, responsive user interface.

## ✨ Features

- **Smart Sinhala Text Processing**: Handles complex Sinhala linguistic rules including Yakaranshaya, Rakaranshaya, and consonant clusters
- **Video-Based Visualization**: Automatic video sequencing to demonstrate complete fingerspelling
- **Modern Web Interface**: Responsive design with beautiful animations and intuitive user experience
- **Clean Architecture**: Modular, object-oriented code structure for easy maintenance and extension
- **Real-time Processing**: Instant conversion and feedback for learning
- **Educational Focus**: Perfect for teachers, students, and sign language enthusiasts

## 🏗️ Architecture

### Backend Components

- **`fingerspelling_rules.py`**: Configuration class with all conversion rules and mappings
- **`fingerspelling_converter.py`**: Main conversion logic with priority-based algorithm
- **`video_processor.py`**: Handles video file mapping and sequence generation
- **`fingerspelling_app.py`**: Main application orchestrator combining all components
- **`app.py`**: Flask web server with RESTful API endpoints

### Frontend Components

- **Modern HTML5 Templates**: Responsive design with Sinhala font support
- **Tailwind CSS Styling**: Beautiful, modern UI with custom animations
- **Vanilla JavaScript**: Clean, efficient client-side interactions
- **Video Player Integration**: Smooth video playback with controls

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Modern web browser with video support

### Installation

1. **Clone or download the project files**
   ```bash
   cd "d:\4th year\Research\Fingerspelling-dataset-testing"
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify your data structure**
   ```
   ├── letters/                    # Video files (.MOV format)
   ├── fingerspelling_mapper.csv   # Video to sign mappings
   ├── fingerspelling_rules.py     # Conversion rules
   ├── fingerspelling_converter.py # Core conversion logic
   ├── video_processor.py          # Video handling
   ├── fingerspelling_app.py       # Main application
   ├── app.py                      # Web server
   ├── templates/                  # HTML templates
   ├── static/                     # CSS, JavaScript, assets
   └── requirements.txt            # Dependencies
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 🎯 Usage

### Basic Usage

1. **Enter a Sinhala word** in the input field (e.g., නම, ගම්මාන, අමල)
2. **Click Convert** or press Enter
3. **View the analysis** showing generated signs and available videos
4. **Play the video sequence** to see the complete fingerspelling

### Advanced Features

- **Sample Words**: Quick-start with pre-loaded examples
- **Batch Processing**: Convert multiple words at once via API
- **Video Controls**: Adjust playback speed, pause, reset
- **Statistics**: View application performance and coverage
- **Demo Mode**: Explore complex linguistic examples

## 🔧 API Endpoints

### Convert Text
```http
POST /api/convert
Content-Type: application/json

{
  "text": "සිංහල වචනය"
}
```

### Batch Convert
```http
POST /api/batch-convert
Content-Type: application/json

{
  "words": ["වචනය1", "වචනය2"]
}
```

### Get Statistics
```http
GET /api/statistics
```

### Get Sample Words
```http
GET /api/samples
```

## 📊 Algorithm Details

The conversion algorithm processes Sinhala text using a priority-based approach:

1. **Priority 1**: Special combinations (Yakaranshaya, Rakaranshaya)
2. **Priority 2**: Consonant + vowel modifier pairs
3. **Priority 3**: Consonant + hal mark combinations
4. **Priority 4**: Skip standalone marks
5. **Priority 5**: Individual character processing

### Supported Features

- ✅ All Sinhala vowels and consonants
- ✅ Yakaranshaya (්‍ය) patterns
- ✅ Rakaranshaya (්‍ր) patterns  
- ✅ Consonant clusters
- ✅ Vowel modifiers
- ✅ Special characters (ං, ෆ්, etc.)

## 📁 File Structure Details

### Core Python Files

- **`fingerspelling_rules.py`**: Contains all linguistic rules, character mappings, and validation logic
- **`fingerspelling_converter.py`**: Implements the conversion algorithm with comprehensive error handling
- **`video_processor.py`**: Manages video file mappings and generates playback sequences
- **`fingerspelling_app.py`**: High-level application interface combining all components

### Web Application Files

- **`app.py`**: Flask web server with API endpoints and static file serving
- **`templates/index.html`**: Main application interface
- **`templates/about.html`**: Information about the project and algorithm
- **`templates/demo.html`**: Interactive examples and demonstrations
- **`static/css/style.css`**: Custom styling with Sinhala font support
- **`static/js/app.js`**: Interactive JavaScript for video playback and UI

## 🎨 Customization

### Adding New Videos

1. Add video files to the `letters/` directory
2. Update `fingerspelling_mapper.csv` with new mappings
3. Restart the application to load new mappings

### Modifying Conversion Rules

1. Edit `fingerspelling_rules.py` to add new signs or rules
2. Update the conversion logic in `fingerspelling_converter.py` if needed
3. Test thoroughly with various input combinations

### Styling Changes

1. Modify `static/css/style.css` for visual changes
2. Update HTML templates for structure changes
3. All styles use Tailwind CSS classes with custom enhancements

## 🐛 Troubleshooting

### Common Issues

**Videos not playing:**
- Check that video files exist in the `letters/` directory
- Verify `fingerspelling_mapper.csv` has correct mappings
- Ensure video files are in supported format (.MOV, .MP4)

**Conversion errors:**
- Check that input text contains valid Sinhala characters
- Review error messages for specific character issues
- Verify `fingerspelling_rules.py` contains required signs

**Application not starting:**
- Install all requirements: `pip install -r requirements.txt`
- Check Python version (3.8+ required)
- Verify all files are present in the correct structure

### Debug Mode

Run with debug enabled for detailed error information:
```bash
python app.py
```

The application will show detailed error messages and validation results on startup.

## 📈 Performance

- **Conversion Speed**: Near-instant processing for typical words
- **Video Loading**: Optimized for smooth playback transitions  
- **Memory Usage**: Efficient handling of video file mappings
- **Scalability**: Supports hundreds of signs and videos

## 🎓 Educational Use

Perfect for:
- **Sign Language Classes**: Interactive learning tool
- **Self-Study**: Practice fingerspelling with immediate feedback
- **Teaching Aids**: Visual demonstration of complex linguistic rules
- **Research**: Understanding Sinhala text processing challenges

## 🤝 Contributing

This project welcomes contributions! Areas for improvement:

- Additional video recordings for missing signs
- Enhanced linguistic rule support
- Mobile app version
- Additional language support
- Performance optimizations

## 📞 Support

For questions, issues, or suggestions:
1. Check the troubleshooting section above
2. Review the algorithm documentation in `/about`
3. Test with the interactive demo at `/demo`

## 📄 License

Educational use permitted. Please credit the original creators when using or modifying this code.

---

**Built with ❤️ for Sinhala Sign Language Learning**