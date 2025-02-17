"""
Vision processor tests.
"""
import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.vision.processor import VisionProcessor

@pytest.fixture
def processor():
    """Create vision processor instance."""
    return VisionProcessor()

@pytest.fixture
def test_image():
    """Create test image."""
    # Create blank image
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw rectangle
    cv2.rectangle(
        image,
        (100, 100),
        (540, 380),
        (255, 255, 255),
        2
    )
    
    # Add text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(
        image,
        "TEST TITLE",
        (200, 200),
        font,
        1,
        (255, 255, 255),
        2
    )
    
    return image

def test_calculate_sharpness(processor, test_image):
    """Test sharpness calculation."""
    # Calculate sharpness
    sharpness = processor.calculate_sharpness(test_image)
    
    assert sharpness > 0

def test_preprocess_image(processor, test_image):
    """Test image preprocessing."""
    # Preprocess image
    processed, data = processor.preprocess_image(test_image)
    
    assert processed is not None
    assert isinstance(data, dict)
    assert "image_size" in data
    assert "sharpness" in data

def test_capture_regions(processor, test_image):
    """Test text region capture."""
    # Capture regions
    regions = processor.capture_regions(test_image)
    
    assert isinstance(regions, list)
    assert len(regions) > 0
    
    region = regions[0]
    assert "text" in region
    assert "coords" in region
    assert len(region["coords"]) == 4

def test_process_image(processor, tmp_path):
    """Test image processing."""
    # Create test image path
    image_path = str(tmp_path / "test.jpg")
    
    # Create test image
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(
        image,
        "TEST",
        (100, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )
    
    # Save image
    cv2.imwrite(image_path, image)
    
    # Process image
    results = processor.process_image(image_path)
    
    assert results["success"]
    assert "vision_data" in results
    assert "texts" in results
    
    # Test with debug
    results = processor.process_image(image_path, debug=True)
    
    assert results["success"]
    assert "debug_image" in results
    assert os.path.exists(results["debug_image"])
    
def test_process_invalid_image(processor):
    """Test processing invalid image."""
    # Process non-existent image
    results = processor.process_image("invalid.jpg")
    
    assert not results["success"]
    assert "error" in results
