"""
Tests for VHS preprocessing pipeline components.
"""
import os
import pytest
import cv2
import numpy as np
from pathlib import Path

from src.vision.preprocessing import (
    FastCLAHE,
    BilateralFilter,
    RegionDetector,
    PreprocessingPipeline,
    ConfidenceScorer,
    TextRegion
)

@pytest.fixture
def test_image():
    """Load test VHS cover image."""
    test_image_path = os.path.join(
        os.path.dirname(__file__),
        'test_data',
        'sample_vhs.jpg'
    )
    return cv2.imread(test_image_path)

def test_fast_clahe():
    """Test CLAHE enhancement."""
    # Create sample grayscale image
    img = np.zeros((100, 100), dtype=np.uint8)
    img[25:75, 25:75] = 128  # Add mid-gray square
    
    clahe = FastCLAHE(clip_limit=1.5, tile_size=(4, 4))
    enhanced = clahe.process(img)
    
    # Verify image was enhanced
    assert enhanced.shape == img.shape
    assert enhanced.dtype == np.uint8
    assert np.mean(enhanced) != np.mean(img)  # Values should change
    
    # Test color image
    color_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    color_enhanced = clahe.process(color_img)
    assert color_enhanced.shape == color_img.shape
    assert color_enhanced.dtype == np.uint8
    
    # Test error handling
    assert clahe.process(None).size == 0  # Invalid input
    invalid_shape = np.zeros((100, 100, 5), dtype=np.uint8)
    assert clahe.process(invalid_shape).shape == invalid_shape.shape  # Invalid channels

def test_bilateral_filter():
    """Test bilateral filtering."""
    img = np.zeros((100, 100), dtype=np.uint8)
    img[25:75, 25:75] = 255  # Add white square
    
    # Add some noise
    noise = np.random.normal(0, 25, img.shape).astype(np.uint8)
    noisy = cv2.add(img, noise)
    
    filter = BilateralFilter(d=7, sigma_color=50, sigma_space=50)
    filtered = filter.process(noisy)
    
    # Verify noise reduction
    assert filtered.shape == img.shape
    assert filtered.dtype == np.uint8
    assert np.std(filtered) < np.std(noisy)  # Less variation
    
    # Test error handling
    assert filter.process(None).size == 0  # Invalid input
    invalid_dims = np.zeros((100, 100, 3, 2), dtype=np.uint8)
    assert filter.process(invalid_dims).shape == invalid_dims.shape  # Invalid dimensions

def test_region_detector():
    """Test text region detection."""
    # Create test image with two text-like regions
    img = np.zeros((200, 200), dtype=np.uint8)
    cv2.putText(img, "TEST", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    cv2.putText(img, "VHS", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    
    detector = RegionDetector(min_area=100, min_width=10, min_height=10)
    regions = detector.detect(img)
    
    # Should find both text regions
    assert len(regions) >= 2
    assert all(isinstance(r, TextRegion) for r in regions)
    assert all(r.width >= 10 and r.height >= 10 for r in regions)
    
    # Test error handling
    assert len(detector.detect(None)) == 0  # Invalid input
    color_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    assert len(detector.detect(color_img)) == 0  # Wrong image type

def test_preprocessing_pipeline(test_image):
    """Test full preprocessing pipeline."""
    pipeline = PreprocessingPipeline()
    preprocessed, regions = pipeline.preprocess(test_image)
    
    # Verify output
    assert isinstance(preprocessed, np.ndarray)
    assert len(preprocessed.shape) == 2  # Should be grayscale
    assert preprocessed.dtype == np.uint8
    assert len(regions) > 0  # Should find some text regions

def test_confidence_scorer():
    """Test confidence scoring for different categories."""
    scorer = ConfidenceScorer()
    
    # Test title scoring
    assert scorer.score_text("The Matrix", "title") > 70  # Valid title with article
    assert scorer.score_text("Spider-Man", "title") > 65  # Valid with hyphen
    assert scorer.score_text("Rocky III", "title") > 70  # Valid with roman numeral
    assert scorer.score_text("Lord of the Rings", "title") > 65  # Valid with conjunction
    assert scorer.score_text("SCREAM!", "title") < 60  # All caps suspicious
    assert scorer.score_text("a", "title") == 20.0  # Too short
    assert scorer.score_text("", "title") == 0  # Empty
    
    # Test year scoring
    assert scorer.score_text("1985", "year") == 100.0  # Valid VHS era
    assert scorer.score_text("1965", "year") == 70.0  # Close to VHS era
    assert scorer.score_text("2025", "year") == 30.0  # Future year
    assert scorer.score_text("abc", "year") <= 30.0  # Invalid format should get low score
    
    # Test runtime scoring
    assert scorer.score_text("120", "runtime") == 100.0  # Typical length
    assert scorer.score_text("45", "runtime") == 70.0  # Short but valid
    assert scorer.score_text("300", "runtime") == 30.0  # Too long
    assert scorer.score_text("xyz", "runtime") <= 30.0  # Invalid format should get low score
    
    # Test rating scoring
    assert scorer.score_text("PG-13", "rating") == 100.0  # Valid rating
    assert scorer.score_text("pg", "rating") == 100.0  # Case-insensitive rating
    assert scorer.score_text("X", "rating") == 0  # Invalid rating
    
    # Test studio scoring
    assert scorer.score_text("Warner Bros. Pictures", "studio") > 65  # Known studio
    assert scorer.score_text("Universal Studios", "studio") > 65  # Known studio
    assert scorer.score_text("Invalid Corp", "studio") < 60  # Unknown studio
    
    # Test director scoring
    assert scorer.score_text("Directed by Steven Spielberg", "director") > 45  # Well-known director
    assert scorer.score_text("Stanley Kubrick", "director") > 45  # Full name
    assert scorer.score_text("Unknown Person", "director") < 50  # Unknown director - adjusted threshold
    
    # Test cast scoring
    assert scorer.score_text("Starring Tom Hanks, Morgan Freeman", "cast") > 80  # Multiple well-known actors
    assert scorer.score_text("Single Name", "cast") < 60  # Insufficient cast info
    
    # Test invalid category
    assert scorer.score_text("test", "invalid") == 0.0

def test_end_to_end_preprocessing(test_image):
    """Test end-to-end preprocessing pipeline with actual VHS cover."""
    pipeline = PreprocessingPipeline()
    preprocessed, regions = pipeline.preprocess(test_image)
    
    # Basic validations
    assert preprocessed is not None
    assert len(regions) > 0
    
    # Check region properties
    for region in regions:
        assert isinstance(region, TextRegion)
        assert region.width >= 10  # Updated min width
        assert region.height >= 10  # Updated min height
        assert region.image.shape[0] == region.height
        assert region.image.shape[1] == region.width
        
        # Region should not be empty
        assert np.any(region.image > 0)

def test_error_handling():
    """Test error handling in preprocessing components."""
    pipeline = PreprocessingPipeline()
    
    # Test with None image
    preprocessed, regions = pipeline.preprocess(None)
    assert preprocessed.size == 0
    assert len(regions) == 0
    
    # Test with empty image
    empty_img = np.array([], dtype=np.uint8)
    preprocessed, regions = pipeline.preprocess(empty_img)
    assert preprocessed.size == 0
    assert len(regions) == 0
    
    # Test with invalid channels
    invalid_img = np.zeros((100, 100, 5), dtype=np.uint8)
    preprocessed, regions = pipeline.preprocess(invalid_img)
    assert preprocessed.shape == invalid_img.shape  # Should return original
    assert len(regions) == 0
    
    # Test with invalid dimensions
    invalid_dims = np.zeros((100, 100, 3, 2), dtype=np.uint8)
    preprocessed, regions = pipeline.preprocess(invalid_dims)
    assert preprocessed.shape == invalid_dims.shape
    assert len(regions) == 0
    
    # Test individual component error handling
    clahe = FastCLAHE()
    assert clahe.process(None).size == 0
    
    bilateral = BilateralFilter()
    assert bilateral.process(None).size == 0
    
    detector = RegionDetector()
    assert len(detector.detect(None)) == 0

def test_preprocessing_performance(test_image):
    """Test preprocessing performance."""
    import time
    
    pipeline = PreprocessingPipeline()
    
    # Measure processing time
    start = time.time()
    preprocessed, regions = pipeline.preprocess(test_image)
    duration = time.time() - start
    
    # Should process reasonably quickly (adjust threshold as needed)
    assert duration < 1.0, f"Preprocessing took {duration:.2f} seconds"
