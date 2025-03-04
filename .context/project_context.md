# Project Context

## Overview
The VHS Auto project processes VHS tape covers and audio media covers, using computer vision for text extraction and external APIs (TMDB, Discogs) for metadata enrichment.

## Core Components

### Vision Processing
- Image preprocessing pipeline with adaptive sizing and quality optimization
- Robust error handling and confidence scoring
- Mock testing infrastructure for vision components

### Media Type Processing
- Movie processing via TMDB API
- Audio media (CD, Vinyl, Cassette) via Discogs API
- Graceful handling of missing API credentials

### User Interface
- Qt-based GUI with results tabs
- Image preview functionality
- Metadata display system

## Recent Improvements

### Vision Pipeline
- Updated coordinator implementation
- Enhanced error handling
- Improved mock data structures
- Comprehensive integration tests

### Testing Coverage
- Mock implementation for vision and API calls
- Error handling validation
- Integration test suite
- Preprocessing pipeline tests

### Code Structure
- Clear component separation
- Robust error handling
- Type hints and documentation
- Environment-based configuration

## Current Focus
1. UI Enhancements
   - Processing status visualization
   - Progress tracking
   - Error messaging improvements

2. Preprocessing Optimization
   - Efficiency improvements
   - Configuration options
   - Caching implementation

3. Testing Extensions
   - Preprocessing coverage
   - Performance benchmarks
   - Test fixtures

## Dependencies
- Python 3.13+
- PyQt6 for GUI
- OpenCV for image processing
- External APIs: TMDB, Discogs
