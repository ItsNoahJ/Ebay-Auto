"""
Tests for OpenCV utility functions.
"""
import cv2
import numpy as np
import pytest
from src.utils.opencv_utils import (
    resize_image,
    enhance_image,
    detect_edges,
    detect_rectangles,
    detect_text_regions,
    apply_adaptive_contrast
)

@pytest.fixture
def sample_image():
    """Create a sample test image."""
    # Create 100x100 grayscale image with text-like patterns
    img = np.zeros((100, 100), dtype=np.uint8)
    
    # Add some text-like rectangles with low contrast
    cv2.rectangle(img, (20, 20), (80, 40), 120, -1)  # Light gray rectangle
    cv2.rectangle(img, (30, 50), (70, 60), 100, -1)  # Slightly darker gray
    
    return img

def test_resize_image_width_only(sample_image):
    """Test resizing with only width specified."""
    width = 200
    resized = resize_image(sample_image, width=width)
    assert resized.shape[1] == width
    assert resized.shape[0] == width  # Should maintain aspect ratio

def test_resize_image_height_only(sample_image):
    """Test resizing with only height specified."""
    height = 200
    resized = resize_image(sample_image, height=height)
    assert resized.shape[0] == height
    assert resized.shape[1] == height  # Should maintain aspect ratio

def test_enhance_image_basic(sample_image):
    """Test basic image enhancement."""
    # Create a larger sample image to avoid auto-scaling
    large_image = cv2.resize(sample_image, (1200, 1200))
    enhanced = enhance_image(large_image)
    assert enhanced.shape == large_image.shape
    assert enhanced.dtype == np.uint8

def test_enhance_image_with_adaptive_contrast(sample_image):
    """Test image enhancement with adaptive contrast."""
    # Create a larger sample image to avoid auto-scaling
    large_image = cv2.resize(sample_image, (1200, 1200))
    enhanced = enhance_image(large_image, adaptive_contrast=True)
    assert enhanced.shape == large_image.shape
    assert enhanced.dtype == np.uint8
    
    # Compare with non-adaptive version
    regular = enhance_image(large_image, adaptive_contrast=False)
    # Should be different due to adaptive processing
    assert not np.array_equal(enhanced, regular)

def test_apply_adaptive_contrast(sample_image):
    """Test adaptive contrast enhancement."""
    # Create image with very low contrast
    low_contrast = sample_image.copy()
    low_contrast[low_contrast > 0] = 110  # Make all non-zero values similar
    
    enhanced = apply_adaptive_contrast(low_contrast)
    
    # Check output properties
    assert enhanced.shape == low_contrast.shape
    assert enhanced.dtype == np.uint8
    
    # Check contrast is improved
    orig_std = np.std(low_contrast)
    enhanced_std = np.std(enhanced)
    assert enhanced_std > orig_std  # Should have more contrast

def test_apply_adaptive_contrast_parameters(sample_image):
    """Test adaptive contrast enhancement with different parameters."""
    # Test with different clip limits
    enhanced1 = apply_adaptive_contrast(sample_image, clip_limit=2.0)
    enhanced2 = apply_adaptive_contrast(sample_image, clip_limit=4.0)
    assert not np.array_equal(enhanced1, enhanced2)
    
    # Test with different grid sizes
    enhanced3 = apply_adaptive_contrast(sample_image, grid_size=(4, 4))
    enhanced4 = apply_adaptive_contrast(sample_image, grid_size=(16, 16))
    assert not np.array_equal(enhanced3, enhanced4)

def test_detect_edges(sample_image):
    """Test edge detection."""
    edges = detect_edges(sample_image)
    assert edges.shape == sample_image.shape
    assert edges.dtype == np.uint8

def test_detect_rectangles(sample_image):
    """Test rectangle detection."""
    edges = detect_edges(sample_image)
    rectangles = detect_rectangles(edges)
    assert isinstance(rectangles, list)
    if len(rectangles) > 0:
        assert isinstance(rectangles[0], np.ndarray)

def test_detect_text_regions(sample_image):
    """Test text region detection."""
    regions = detect_text_regions(sample_image)
    assert isinstance(regions, list)
    if len(regions) > 0:
        x, y, w, h = regions[0]
        assert all(isinstance(v, int) for v in (x, y, w, h))
