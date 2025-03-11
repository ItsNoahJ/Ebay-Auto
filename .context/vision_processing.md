# Vision Processing Pipeline

## Overview

The vision processing system uses a multi-stage pipeline to enhance image quality and extract text from VHS covers. Each stage's output is now visualized in the GUI to help users understand the processing steps.

## Pipeline Stages

1. **Original**: The raw input image 
2. **Grayscale**: Converted to grayscale for text processing
3. **Enhanced**: Improved using adaptive contrast and noise reduction
4. **Text**: Final preprocessed image ready for OCR

## Implementation Details

- `PreprocessingPipeline` manages the image enhancement steps and stores intermediate results
- `VHSVision` handles OCR using LM Studio and preserves preprocessing stages
- `VisionProcessor` acts as a bridge, managing preprocessing and OCR coordination
- `ProcessingCoordinator` converts OpenCV images (both color and grayscale) to Qt format for display
- `ResultsView` displays the stages in a scrollable interface

## Image Display

The GUI now shows a visual pipeline of the preprocessing stages:
- Left to right progression showing transformation of the image
- Each stage labeled for clear understanding
- Support for both color and grayscale image formats
- Real-time updates as processing occurs

## Future Improvements

Potential enhancements to consider:
- Add tooltips explaining each preprocessing stage
- Include confidence scores for each stage's effectiveness
- Allow user adjustment of preprocessing parameters
- Export preprocessed images for debugging
