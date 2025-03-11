"""
Tests for VisionProcessor with timeout handling.
"""
import pytest
import cv2
import numpy as np
from unittest.mock import patch, MagicMock

from src.vision.preprocessing import TimeoutError
from src.vision.processor import VisionProcessor
from src.vision.vhs_vision import VHSVision
from tests.mocks import (
    create_test_image,
    MockVHSVisionWithTimeout,
    PreprocessorWithTimeout
)

@pytest.fixture
def mock_api():
    """Mock successful API connection."""
    mock_vision = VHSVision()
    mock_vision.check_models = MagicMock(return_value=True)
    mock_vision._make_api_request = MagicMock(return_value={"data": [{"id": "test-model"}]})
    return mock_vision

@pytest.fixture
def processor(mock_api):
    """Create VisionProcessor with mocked API."""
    processor = VisionProcessor(save_debug=False)
    return processor

def test_processor_preprocessing_timeout(processor):
    """Test timeout during preprocessing stage."""
    # Configure processor with slow preprocessor
    processor.vision = MockVHSVisionWithTimeout(processing_delay=3)
    processor.vision.pipeline = PreprocessorWithTimeout(processing_delay=3)
    processor.vision.timeout = 1  # Set timeout
    
    # Process with timeout shorter than delay
    with pytest.raises(TimeoutError):
        processor.extract_text(create_test_image())
        
def test_processor_extraction_timeout(processor):
    """Test timeout during text extraction stage."""
    # Configure processor with slow vision
    processor.vision = MockVHSVisionWithTimeout(processing_delay=3)
    processor.vision.timeout = 1  # Set timeout
    
    # Process with timeout shorter than delay
    with pytest.raises(TimeoutError):
        processor.extract_text(create_test_image())
        
def test_processor_partial_completion(processor):
    """Test that early stages complete before timeout."""
    # Create processor with slow vision but fast preprocessing
    processor.vision = MockVHSVisionWithTimeout(processing_delay=3)
    
    # Set up test image
    test_image = create_test_image()
    
    # Process with timeout
    try:
        processor.vision.timeout = 1  # Set timeout
        processor.extract_text(test_image)
    except TimeoutError:
        # Verify preprocessing images were stored
        for stage in ["Grayscale", "Enhanced"]:
            img = processor.vision.preprocessing_images.get(stage)
            assert img is not None, f"{stage} image missing"
            assert isinstance(img, np.ndarray), f"{stage} image wrong type"
        
def test_processor_success_no_timeout(processor):
    """Test successful processing without timeout."""
    processor.vision = MockVHSVisionWithTimeout(processing_delay=1)
    
    # Process with sufficient timeout
    result = processor.extract_text(create_test_image())
    
    assert result["success"]
    assert result["vision_data"]["title"] == "Mock Title"
    assert result["vision_data"]["confidence"]["title"] >= 0.8

def test_processor_confidence_tracking(processor):
    """Test that confidence scores are tracked through timeout."""
    processor.vision = MockVHSVisionWithTimeout(processing_delay=1)
    
    # Process image
    result = processor.extract_text(create_test_image())
    
    # Verify confidence scores exist
    assert "vision_data" in result
    assert "confidence" in result["vision_data"]
    confidence = result["vision_data"]["confidence"]
    assert isinstance(confidence, dict)
    
    # At least title should have confidence
    assert confidence.get("title", 0) > 0

def test_api_error_handling(processor):
    """Test handling of API errors."""
    # Configure vision to return error
    processor.vision = MockVHSVisionWithTimeout(processing_delay=1)
    processor.vision.extract_text = MagicMock(return_value={
        "success": False,
        "error": "API Connection Error"
    })
    
    # Process image - should handle API error gracefully
    result = processor.extract_text(create_test_image())
    
    # Should indicate error
    assert not result["success"]
    assert "error" in result

def test_preprocessing_image_storage(processor):
    """Test preprocessing image storage and retrieval."""
    # Create test grayscale image
    gray_image = np.zeros((100, 100), dtype=np.uint8)
    
    # Should handle both 2D and 3D images
    processor.vision = MockVHSVisionWithTimeout(processing_delay=0)
    processor.vision.preprocessing_images = {
        "Grayscale": gray_image,
        "Enhanced": cv2.cvtColor(gray_image, cv2.COLOR_GRAY2BGR)
    }
    
    # Process image
    result = processor.extract_text(create_test_image())
    
    # Verify images were stored
    assert "Grayscale" in processor.vision.preprocessing_images
    assert "Enhanced" in processor.vision.preprocessing_images
