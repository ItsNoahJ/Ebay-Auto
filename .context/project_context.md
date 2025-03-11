# Project Context

## Overview
The VHS Auto project processes VHS tape covers and audio media covers, using computer vision for text extraction and external APIs (TMDB, Discogs) for metadata enrichment.

## Core Components

### Vision Processing
- Advanced preprocessing pipeline with multi-stage denoising and edge preservation
- FastCLAHE contrast enhancement and statistical normalization
- Intelligent text region detection with confidence scoring
- Comprehensive test suite with performance benchmarks
- High-resolution processing (1600px width) optimized for text extraction

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
- Modular preprocessing system with specialized components
- Enhanced text region detection and validation
- Improved confidence scoring with category-specific rules
- Comprehensive error handling and debug logging
- Extensive test coverage for all components

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

2. Vision System Improvements
   - Neural-based denoising integration
   - Dynamic parameter optimization
   - Layout-aware processing
   - Real-time quality assessment
   - Performance optimization for batch processing

3. Testing Extensions
   - Preprocessing coverage
   - Performance benchmarks
   - Test fixtures

## Dependencies
- Python 3.13+
- PyQt6 for GUI
- OpenCV 4.x with contrib modules for advanced image processing
- LM Studio for vision-language processing
- External APIs: TMDB, Discogs
- NumPy for efficient array operations
