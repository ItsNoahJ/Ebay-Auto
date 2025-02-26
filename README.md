# VHS Tape Scanner

An application for scanning and digitizing VHS tape covers using computer vision and OCR.

## Setup Instructions

### Prerequisites

1. Install Python 3.8+ and pip
2. Install [LM Studio](https://lmstudio.ai/) for vision processing
3. Get a TMDB API key from [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)

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

4. Edit `.env` and set:
- `TMDB_API_KEY`: Your TMDB API key
- Other settings as needed

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
- Movie information lookup via TMDB API
- Debug visualization of processing steps
- Results export to JSON

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

2. "TMDB client disabled"
   - Verify your TMDB API key in .env
   - Check internet connection
   - Ensure the API key has proper permissions

3. "No text extracted"
   - Try adjusting image lighting and angle
   - Check if the image is clear and focused
   - Verify text is visible in the debug output images

## License

This project is licensed under the MIT License - see the LICENSE file for details.
