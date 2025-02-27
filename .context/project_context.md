# Project Context

## Overview
The VHS Auto project is a system for processing VHS tape covers and audio media covers. It uses computer vision to extract text and integrates with external APIs (TMDB for movies, Discogs for audio) to fetch metadata.

## Core Components

### Vision Processing
- Uses LM Studio for text extraction
- Implements preprocessing steps for better OCR results
- Handles image enhancement and cleanup

### Media Type Processing
- Movie processing via TMDB API
- Audio media (CD, Vinyl, Cassette) via Discogs API
- Graceful handling of missing API credentials

### User Interface
- Qt-based GUI with tabs for different types of results
- Preview of processed images
- Detailed display of extracted metadata

## Recent Improvements

### Test Coverage
- Integration tests for both movie and audio processing pipelines
- Mock implementation for vision processing and API calls
- Error handling tests for invalid images and missing API keys
- Improved handling of None values in result display

### Code Structure
- Clear separation between vision processing and metadata enrichment
- Robust error handling throughout the pipeline
- Type hints and documentation for key functions
- Environment variable configuration for API credentials

### Known Issues
- See ocr_challenges.md for specific OCR-related challenges
- GUI performance could be optimized for large batch processing

## Next Steps
1. Implement batch processing capabilities
2. Add support for barcode scanning
3. Improve error recovery in the vision pipeline
4. Consider caching mechanism for API results

## Testing Strategy
- Unit tests for individual components
- Integration tests for full processing pipeline
- Mock external dependencies (APIs, vision processing)
- GUI testing with Qt test framework

## Dependencies
- Python 3.13+
- PyQt6 for GUI
- OpenCV for image processing
- LM Studio for text extraction
- External APIs: TMDB, Discogs
