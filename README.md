# VHS Tape Processor

An automated system for processing and identifying VHS tapes using computer vision and movie metadata.

## Features

- Capture images of VHS tapes using a mounted camera
- Extract text from tape covers using OCR
- Identify movies using TMDb API
- Debug visualization of detected regions
- CLI and GUI interfaces (GUI coming soon)
- Result storage and caching

## Requirements

- Python 3.8+
- OpenCV
- Tesseract OCR
- TMDb API key

### Windows

1. Install Python 3.8 or higher
2. Install Tesseract OCR:
   - Download installer from https://github.com/UB-Mannheim/tesseract/wiki
   - Install to default location (`C:\Program Files\Tesseract-OCR`)
3. Set up environment:
   ```bat
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Linux/macOS

1. Install Python 3.8 or higher
2. Install Tesseract OCR:
   ```bash
   # Ubuntu/Debian
   sudo apt install tesseract-ocr
   
   # macOS
   brew install tesseract
   ```
3. Set up environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Configuration

1. Copy example environment file:
   ```bash
   cp .env.example .env
   ```

2. Configure settings in `.env`:
   - Set `TESSERACT_CMD` to Tesseract executable path
   - Add your TMDb API key as `TMDB_API_KEY`
   - Adjust other settings as needed

## Usage

### Command Line

Process a single image:
```bash
python -m src.cli path/to/image.jpg
```

Enable debug output:
```bash
python -m src.cli path/to/image.jpg --debug
```

### Development

Create test image:
```bash
python create_test_image.py "Movie Title" "1995" -o test.jpg
```

Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src
```

## Project Structure

```
├── src/
│   ├── config/         # Configuration
│   ├── enrichment/     # Movie data enrichment
│   ├── gui/           # GUI components (coming soon)
│   ├── hardware/      # Camera interface
│   ├── models/        # Core processing
│   ├── utils/         # Utility functions
│   └── vision/        # Computer vision
├── tests/             # Test suite
├── storage/           # Results and cache
│   ├── cache/         # API cache
│   ├── images/        # Captured images
│   └── results/       # Processing results
└── test_images/       # Test data
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
