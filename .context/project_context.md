# VHS Vision Processing Project Context

## Current Status

The project focuses on extracting text information from VHS cover images using computer vision and LM Studio's API. Recent optimizations have significantly improved processing speed and reliability.

### Core Components

1. **VHSVision Class** (src/vision/lmstudio_vision.py)
   - Handles image preprocessing and text extraction
   - Optimized for speed and memory efficiency
   - Includes adaptive image sizing and quality
   - Uses LM Studio's API for text recognition

2. **Performance Characteristics**
   - Preprocessing: ~260ms per image
   - Image encoding: ~3ms average
   - API response: 15s timeout (reduced from 30s)
   - Memory usage: <1GB per operation

3. **Testing Infrastructure**
   - Comprehensive performance benchmarks
   - Automated test suite with mocked API calls
   - Documented in tests/test_performance.py

## Architecture Decisions

1. **Image Processing Pipeline**
   - GPU-optimized dimension handling (32-pixel alignment)
   - Minimum dimension enforcement (320px)
   - Adaptive JPEG quality (65-95%)
   - CLAHE for contrast enhancement

2. **API Integration**
   - Streamlined prompts for faster inference
   - Caching support via content hashing
   - Improved error handling and diagnostics
   - Optimized request payloads

3. **Quality Assurance**
   - Confidence scoring for extracted text
   - Debug image output for verification
   - Performance monitoring and benchmarks

## Current Challenges

1. **Processing Speed**
   - Balancing quality vs. speed in preprocessing
   - API response time variability
   - Memory usage optimization

2. **Text Recognition**
   - Handling low contrast covers
   - Dealing with cursive/stylized text
   - Multiple text regions handling

## Next Steps

1. **Short Term**
   - Add batch processing support
   - Implement response caching with TTL
   - Add detailed timing breakdowns

2. **Long Term**
   - Explore WebP format adoption
   - Consider async processing
   - Add automated parameter tuning
