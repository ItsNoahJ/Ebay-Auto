# VHS Tape Scanner

An application for scanning and digitizing VHS tape covers using computer vision and OCR.

## Setup Instructions

### Prerequisites

1. Install Python 3.8+ and pip
2. Install [LM Studio](https://lmstudio.ai/) for vision processing
3. (Optional) Get API keys for metadata enrichment:
   - TMDB API key from [www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)
   - Discogs API access from [www.discogs.com/settings/developers](https://www.discogs.com/settings/developers)

### Installation

1. Clone this repository:
```bash
git clone [repository-url]
cd [repository-directory]
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

4. (Optional) Edit `.env` and set:
- `TESSERACT_PATH`: Path to Tesseract OCR executable
- `DEBUG`: Set to "true" for debug output

Note: API keys can now be configured directly in the application's settings dialog.

### Running LM Studio

1. Start LM Studio
2. Load the `lmstudio-community/minicpm-o-2_6` model
3. Ensure the API server is running on `http://127.0.0.1:1234`

### Running the Application

1. Start the GUI:
```bash
python run_gui.py
```

2. Or run with a specific image:
```bash
python run_gui.py path/to/image.jpg
```

## Features

- VHS cover text extraction using LM Studio vision model
- Optional metadata enrichment:
  - Movie information lookup via TMDB API
  - Music information lookup via Discogs API
- Debug visualization of processing steps
- Results export to JSON

## Configuration

### API Settings

The application includes a settings dialog (File > Settings) where you can configure:

1. TMDB API Integration (Optional)
   - Enter your TMDB API key
   - Test the connection
   - Use for movie metadata lookup

2. Discogs API Integration (Optional)
   - Enter your Discogs Consumer Key and Secret
   - Test the connection
   - Use for music metadata lookup

Note: Both APIs are optional. The application will work without them but won't fetch additional metadata.

## Development

- Run tests: `pytest`
- Debug output is saved to `debug_output/`
- Logs are in `debug.log.txt`

## Troubleshooting

### Common Issues

1. "Could not connect to LM Studio"
   - Make sure LM Studio is running
   - Verify the model is loaded
   - Check if the API server is running on port 1234

2. "API integration disabled"
   - Open Settings dialog and verify API keys
   - Check internet connection
   - Test connection using the "Test Key" buttons
   - For Discogs, ensure both Consumer Key and Secret are entered

3. "No text extracted"
   - Try adjusting image lighting and angle
   - Check if the image is clear and focused
   - Verify text is visible in the debug output images

## License

This project is licensed under the MIT License - see the LICENSE file for details.
