"""
Tests for VHS title extraction preprocessing components.
"""
import os
import pytest
import cv2
import numpy as np
import logging
from pathlib import Path
from src.vision.preprocessing import TextRegion

from src.vision.vhs_vision import VHSVision

logger = logging.getLogger(__name__)

@pytest.fixture
def vision():
    """Initialize VHSVision with debug enabled."""
    return VHSVision(save_debug=True)

@pytest.fixture
def test_image():
    """Load test VHS cover image."""
    test_path = "testvhs3.jpg"
    if not os.path.exists(test_path):
        pytest.skip("Test image not found")
    return cv2.imread(test_path)

@pytest.mark.skip(reason="LM Studio API integration not being tested")
def test_title_extraction(vision, test_image):
    """Test title extraction with optimized preprocessing."""
    result = vision.extract_info(test_image, "title")
    
    assert result is not None
    assert isinstance(result, dict)
    assert "text" in result
    assert "confidence" in result
    assert "validated" in result
    
    # Title should be extracted with reasonable confidence
    assert result["text"], "Title should not be empty"
    assert result["confidence"] > 60, "Title confidence should be reasonable"
    assert result["validated"], "Result should be validated"

@pytest.mark.skip(reason="LM Studio API integration not being tested")
def test_year_extraction(vision, test_image):
    """Test year extraction with optimized preprocessing."""
    result = vision.extract_info(test_image, "year")
    
    assert result is not None
    assert "text" in result
    
    if result["text"]:
        # Year format validation
        year = result["text"]
        assert len(year) == 4, "Year should be 4 digits"
        assert year.isdigit(), "Year should be numeric"
        assert 1970 <= int(year) <= 2006, "Year should be in VHS era"
        assert result["confidence"] > 50, "Year confidence should be reasonable"

@pytest.mark.skip(reason="LM Studio API integration not being tested")
def test_rating_extraction(vision, test_image):
    """Test rating extraction with optimized preprocessing."""
    result = vision.extract_info(test_image, "rating")
    
    assert result is not None
    assert "text" in result
    
    if result["text"]:
        rating = result["text"].upper()
        valid_ratings = ["G", "PG", "PG-13", "R", "NC-17"]
        assert rating in valid_ratings, f"Rating {rating} should be valid MPAA rating"
        assert result["confidence"] > 50, "Rating confidence should be reasonable"

@pytest.mark.skip(reason="LM Studio API integration not being tested")
def test_runtime_extraction(vision, test_image):
    """Test runtime extraction with optimized preprocessing."""
    result = vision.extract_info(test_image, "runtime")
    
    assert result is not None
    assert "text" in result
    
    if result["text"]:
        runtime = result["text"]
        assert runtime.isdigit(), "Runtime should be numeric"
        minutes = int(runtime)
        assert 60 <= minutes <= 240, "Runtime should be reasonable movie length"
        assert result["confidence"] > 50, "Runtime confidence should be reasonable"

def test_preprocessing_output(vision, test_image):
    """Test preprocessing pipeline outputs valid images and regions."""
    # Access pipeline directly to test preprocessing
    preprocessed, regions = vision.pipeline.preprocess(test_image)
    
    # Verify preprocessed image
    assert isinstance(preprocessed, np.ndarray)
    assert len(preprocessed.shape) == 2  # Should be grayscale
    assert preprocessed.dtype == np.uint8
    assert preprocessed.size > 0
    
    # Verify detected regions
    assert len(regions) > 0
    for region in regions:
        assert isinstance(region, TextRegion)
        assert region.width >= 10  # Min width
        assert region.height >= 10  # Min height
        assert region.image.shape[0] == region.height
        assert region.image.shape[1] == region.width
        assert np.any(region.image > 0)  # Should not be empty

def test_debug_output(vision, test_image):
    """Test debug image output."""
    debug_dir = Path("debug_output")
    if debug_dir.exists():
        for f in debug_dir.glob("*"):
            f.unlink()
    
    # Process image with debug enabled
    preprocessed, regions = vision.pipeline.preprocess(test_image)
    vision.save_debug_image(preprocessed, "test_preprocessing")
    
    # Check debug images were saved
    assert debug_dir.exists()
    debug_files = list(debug_dir.glob("*.jpg"))
    assert len(debug_files) > 0
    
    # Verify debug image format
    for img_path in debug_files:
        img = cv2.imread(str(img_path))
        assert img is not None
        assert img.shape[0] > 0 and img.shape[1] > 0

def test_error_handling(vision):
    """Test error handling with invalid inputs."""
    # Test with None image
    preprocessed, regions = vision.pipeline.preprocess(None)
    assert preprocessed.size == 0
    assert len(regions) == 0
    
    # Test with empty image
    empty_img = np.array([], dtype=np.uint8)
    preprocessed, regions = vision.pipeline.preprocess(empty_img)
    assert preprocessed.size == 0
    assert len(regions) == 0
    
    # Test with invalid channels
    invalid_img = np.zeros((100, 100, 5), dtype=np.uint8)
    preprocessed, regions = vision.pipeline.preprocess(invalid_img)
    assert len(regions) == 0

def test_performance(vision, test_image):
    """Test preprocessing performance."""
    import time
    
    # Test preprocessing pipeline performance
    start = time.time()
    preprocessed, regions = vision.pipeline.preprocess(test_image)
    duration = time.time() - start
    
    # Should process reasonably quickly
    assert duration < 1.0, f"Preprocessing took {duration:.2f} seconds"
    
    # Verify output quality
    assert preprocessed.size > 0
    assert len(regions) > 0
    assert all(r.width >= 10 and r.height >= 10 for r in regions)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    pytest.main([__file__, "-v"])
