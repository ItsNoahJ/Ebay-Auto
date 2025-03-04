"""
Unit tests for VHS preprocessing pipeline.
"""
import pytest
import numpy as np
import cv2

from src.vision.preprocessing import (
    TextRegion,
    FastCLAHE,
    BilateralFilter,
    RegionDetector,
    ConfidenceScorer,
    PreprocessingPipeline
)

@pytest.fixture
def sample_image():
    """Create a sample test image with text-like regions."""
    # Create 200x300 grayscale image
    image = np.zeros((200, 300), dtype=np.uint8)
    
    # Add rectangular regions that could be text
    cv2.putText(image, "TITLE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    cv2.putText(image, "2024", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    cv2.putText(image, "120 min", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    
    return image

@pytest.fixture
def noisy_image(sample_image):
    """Add noise to sample image."""
    noise = np.random.normal(0, 25, sample_image.shape).astype(np.uint8)
    noisy = cv2.add(sample_image, noise)
    return noisy

def test_fast_clahe():
    """Test CLAHE contrast enhancement."""
    # Create test image with poor contrast
    image = np.zeros((100, 100), dtype=np.uint8)
    image[25:75, 25:75] = 50  # Mid-gray rectangle
    
    clahe = FastCLAHE(clip_limit=2.0, grid_size=(8,8))
    enhanced = clahe.process(image)
    
    # Enhanced image should have greater contrast
    assert np.std(enhanced) > np.std(image)
    assert enhanced.dtype == np.uint8

def test_bilateral_filter(noisy_image):
    """Test bilateral filtering."""
    bilateral = BilateralFilter(d=5, sigma_color=25, sigma_space=25)
    filtered = bilateral.process(noisy_image)
    
    # Check noise reduction in uniform areas while preserving edges
    uniform_region = filtered[0:20, 0:20]  # Get corner region
    assert np.std(uniform_region) < np.std(noisy_image[0:20, 0:20])
    assert filtered.dtype == np.uint8

def test_region_detector(sample_image):
    """Test text region detection."""
    detector = RegionDetector(
        min_area=50,
        max_area_ratio=0.5,
        min_aspect=0.1,
        max_aspect=10.0
    )
    
    regions = detector.detect(sample_image)
    
    # Should detect the text regions we added
    assert len(regions) >= 3  # At least our 3 text items
    
    # Verify region properties
    for region in regions:
        assert isinstance(region, TextRegion)
        assert region.width > 0 and region.height > 0
        assert region.image is not None
        assert region.image.dtype == np.uint8

def test_confidence_scorer():
    """Test confidence scoring for different categories."""
    scorer = ConfidenceScorer()
    
    # Test year scoring
    assert scorer.score_text("2024", "year") >= 90.0  # Valid year
    assert scorer.score_text("202", "year") < 90.0    # Invalid year
    
    # Test runtime scoring
    assert scorer.score_text("120", "runtime") >= 85.0  # Valid runtime
    assert scorer.score_text("500", "runtime") < 85.0   # Invalid runtime
    
    # Test rating scoring
    assert scorer.score_text("PG-13", "rating") >= 95.0  # Valid rating
    assert scorer.score_text("ABC", "rating") < 95.0     # Invalid rating
    
    # Test empty text
    assert scorer.score_text("", "title") == 0.0

def test_preprocessing_pipeline(noisy_image):
    """Test complete preprocessing pipeline."""
    pipeline = PreprocessingPipeline()
    
    # Process image
    processed, regions = pipeline.preprocess(noisy_image)
    
    # Verify output types
    assert isinstance(processed, np.ndarray)
    assert isinstance(regions, list)
    assert all(isinstance(r, TextRegion) for r in regions)
    
    # Check image properties
    assert len(processed.shape) == 2  # Should be grayscale
    assert processed.dtype == np.uint8
    
    # Verify improved quality
    assert np.std(processed) < np.std(noisy_image)  # Less noise
    
    # Test error handling
    invalid_image = np.array([])
    processed_invalid, regions_invalid = pipeline.preprocess(invalid_image)
    assert isinstance(processed_invalid, np.ndarray)
    assert regions_invalid == []

def test_text_region_dataclass():
    """Test TextRegion dataclass functionality."""
    # Create sample region
    region = TextRegion(
        x=10,
        y=20,
        width=100,
        height=50,
        image=np.zeros((50, 100), dtype=np.uint8),
        confidence=0.85
    )
    
    # Verify properties
    assert region.x == 10
    assert region.y == 20
    assert region.width == 100
    assert region.height == 50
    assert isinstance(region.image, np.ndarray)
    assert region.confidence == 0.85

def test_pipeline_with_color_image():
    """Test pipeline with color input image."""
    # Create color test image
    color_image = np.zeros((200, 300, 3), dtype=np.uint8)
    color_image[50:150, 50:250] = [0, 0, 255]  # Red rectangle
    
    pipeline = PreprocessingPipeline()
    processed, regions = pipeline.preprocess(color_image)
    
    # Verify conversion to grayscale
    assert len(processed.shape) == 2
    assert processed.dtype == np.uint8
    
    # Should still detect the rectangle
    assert len(regions) > 0

def test_pipeline_error_handling():
    """Test error handling in pipeline."""
    pipeline = PreprocessingPipeline()
    
    # Test with invalid inputs
    assert pipeline.preprocess(None) == (None, [])
    assert pipeline.preprocess(np.array([])) == (np.array([]), [])
    
    # Test with invalid image type
    float_image = np.random.rand(100, 100).astype(np.float32)
    processed, regions = pipeline.preprocess(float_image)
    assert processed.dtype == np.uint8  # Should convert to uint8
