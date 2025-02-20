# eBay Media Processor

A desktop application for streamlining eBay listings of physical media items (VHS, DVDs, CDs, etc.) using computer vision and OCR.

## Features

- Automatic media type detection (VHS, DVD, CD)
- Text extraction using OCR (titles, years, runtime)
- Barcode scanning and database lookup
- Progress tracking and debug visualization
- Local database storage
- Modern dark-themed GUI

## Requirements

- Python 3.10+
- Tesseract OCR
- ZBar (for barcode scanning)

### System Dependencies

1. Install Tesseract OCR:
   - Windows: Download and install from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - Mac: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`

2. Install ZBar:
   - Windows: Download and install from [here](https://sourceforge.net/projects/zbar/files/zbar/0.10/)
   - Mac: `brew install zbar`
   - Linux: `sudo apt-get install libzbar0`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ebay-media-processor.git
   cd ebay-media-processor
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python run_app.py
   ```

2. Select a media image using the "Choose File" button
3. Click "Process Image" to analyze
4. Review detected information and create eBay listing

## Configuration

- Environment variables in `.env`:
  ```
  DEBUG=False
  TESSERACT_PATH=/usr/bin/tesseract  # Adjust for your system
  ```

## Development

### Project Structure

```
ebay-media-processor/
├── src/
│   ├── barcode/         # Barcode detection
│   ├── flet_gui/        # GUI components
│   ├── models/          # Database models
│   ├── vision/          # Image processing
├── tests/               # Unit tests
├── .env                 # Environment variables
├── requirements.txt     # Dependencies
```

### Running Tests

```bash
pytest tests/
```

### Debug Output

Debug images are saved to `debug_output/` showing each processing stage:
- Original image
- Grayscale conversion
- Enhanced contrast
- Character regions
- Detected barcodes

## Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details
