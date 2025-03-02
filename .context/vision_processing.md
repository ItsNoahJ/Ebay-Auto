# Vision Processing Documentation

## Overview
The vision processing system uses a combination of image preprocessing and LM Studio's vision capabilities to extract information from VHS covers. The system is designed to balance accuracy, speed, and reliability.

## Key Components

### 1. VHSVision Class
Located in `src/vision/lmstudio_vision.py`, this is the core vision processing component.

#### Confidence Calculation
The system uses a sophisticated confidence scoring system:

##### Title Length Confidence
- Base confidence for titles (1-6 words): 0.7
- Titles > 6 words receive:
  - Base penalty: 0.3 base confidence
  - Progressive penalty: -0.1 per additional word (max -0.2)
  - No capitalization boost for long titles
- Additional modifiers:
  - +0.2 for proper capitalization (short titles only)
  - -0.1 for trailing punctuation

##### Year Confidence
- Base confidence for valid year: 0.9
- +0.1 bonus for VHS era years (1970-2020)

##### Runtime Confidence
- Base confidence for any time format: 0.8
- +0.2 bonus for complete HH:MM format

### 2. Image Preprocessing
The system applies several preprocessing steps to optimize text extraction:

```python
# Example preprocessing pipeline
image = preprocess_image(input_image)
# 1. Grayscale conversion
# 2. Adaptive sizing (target: 640x480)
# 3. CLAHE enhancement (clipLimit=1.5, tileGridSize=4x4)
# 4. Denoising
# 5. Morphological operations for text clarity
# 6. Final sharpening
```

### 3. Integration Points

#### VisionProcessor Class
- Manages the high-level processing pipeline
- Handles confidence thresholds for API backup
- Default threshold: 70% confidence

#### ProcessingCoordinator
- Coordinates between vision and GUI components
- Manages result storage and validation
- Handles error cases and debugging output
- Implements fallback mechanisms for failed extractions

#### GUI Integration
- Displays confidence levels in results view
- Enables save action regardless of confidence
- Shows processing status and error handling

## Configuration

### Debug Mode
Enable debug mode to save intermediate processing steps:
```python
vision = VHSVision(save_debug=True)
```

### Processing Settings
```python
# Target image size (px)
target_pixel_count = 307200  # 640x480

# Target encoded size (bytes)
target_encoded_size = 170000  # For 2048 tokens

# JPEG quality
quality_range = (65, 95)  # Adaptive based on size
```

## Error Handling
The system includes comprehensive error handling:
- Invalid image detection
- LM Studio connection monitoring
- Graceful degradation for low confidence results
- Automatic API backup for low confidence fields

## Testing
Integration tests verify:
1. Confidence Calculation
   - Normal title processing (high confidence)
   - Long title handling (low confidence)
   - Field-specific confidence thresholds

2. Error Handling
   - Missing file errors
   - Processing failures
   - Invalid image data
   - API connection issues

3. Pipeline Validation
   - End-to-end preprocessing flow
   - Mock vision responses
   - Data structure integrity
   - Coordinator integration

Run tests with:
```bash
python -m pytest tests/test_vision_integration.py -v
```

Mock classes in `tests/mocks.py` provide consistent test data:
- MockVisionProcessor: Standard high-confidence results
- MockLongTitleProcessor: Low-confidence long title cases
- MockErrorProcessor: Various error scenarios

## Performance Considerations
- Image resizing balances quality and processing speed
- Adaptive JPEG quality for optimal token usage
- Progressive confidence penalties prevent false positives
- Parallel processing for GUI responsiveness

## Best Practices
1. Always verify LM Studio connection before processing
2. Monitor confidence scores for system health
3. Enable debug mode during development
4. Check both vision and API results in low confidence cases
