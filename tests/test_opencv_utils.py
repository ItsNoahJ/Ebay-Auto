"""
Unit tests for OpenCV utility functions.
"""
import pytest
import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.utils import opencv_utils

@pytest.fixture
def sample_image():
    """Create a sample test image."""
    # Create a 100x100 RGB test image
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    # Add some features to test processing
    cv2.rectangle(image, (20, 20), (80, 80), (255, 255, 255), -1)
    cv2.circle(image, (50, 50), 20, (128, 128, 128), -1)
    return image

@pytest.fixture
def noisy_image():
    """Create a noisy test image."""
    # Create base image
    image = np.zeros((100, 100), dtype=np.uint8)
    cv2.rectangle(image, (20, 20), (80, 80), 255, -1)
    
    # Add noise
    noise = np.random.normal(0, 25, image.shape).astype(np.uint8)
    noisy = cv2.add(image, noise)
    return noisy

@pytest.mark.unit
def test_load_image_success(tmp_path):
    """Test loading a valid image file."""
    # Create a temporary test image
    image_path = tmp_path / "test.jpg"
    test_image = np.zeros((10, 10, 3), dtype=np.uint8)
    cv2.imwrite(str(image_path), test_image)
    
    # Load the image
    loaded = opencv_utils.load_image(str(image_path))
    assert loaded is not None
    assert loaded.shape == (10, 10, 3)

@pytest.mark.unit
def test_load_image_nonexistent():
    """Test loading a non-existent image file."""
    loaded = opencv_utils.load_image("nonexistent.jpg")
    assert loaded is None

@pytest.mark.unit
def test_convert_to_grayscale_rgb(sample_image):
    """Test grayscale conversion of RGB image."""
    gray = opencv_utils.convert_to_grayscale(sample_image)
    assert len(gray.shape) == 2
    assert gray.shape == (100, 100)

@pytest.mark.unit
def test_convert_to_grayscale_already_gray(sample_image):
    """Test grayscale conversion of already grayscale image."""
    gray1 = opencv_utils.convert_to_grayscale(sample_image)
    gray2 = opencv_utils.convert_to_grayscale(gray1)
    assert np.array_equal(gray1, gray2)

@pytest.mark.unit
def test_resize_image_larger(sample_image):
    """Test resize of image larger than target width."""
    large_image = cv2.resize(sample_image, (2000, 1000))
    resized = opencv_utils.resize_image(large_image, target_width=1024)
    assert resized.shape[1] == 1024  # Width should be target
    assert resized.shape[0] == 512   # Height should maintain aspect ratio

@pytest.mark.unit
def test_resize_image_smaller(sample_image):
    """Test resize of image smaller than target width."""
    small_image = cv2.resize(sample_image, (500, 250))
    resized = opencv_utils.resize_image(small_image, target_width=1024)
    assert resized.shape == (250, 500, 3)  # Should not change size

@pytest.mark.unit
def test_enhance_contrast(sample_image):
    """Test contrast enhancement."""
    gray = opencv_utils.convert_to_grayscale(sample_image)
    enhanced = opencv_utils.enhance_contrast(gray)
    
    # Enhanced image should have greater standard deviation
    assert np.std(enhanced) > np.std(gray)

@pytest.mark.unit
def test_denoise_image(noisy_image):
    """Test multi-stage image denoising."""
    denoised = opencv_utils.denoise_image(noisy_image)
    
    # Test overall noise reduction
    roi_noisy = noisy_image[30:70, 30:70]  # Center region
    roi_denoised = denoised[30:70, 30:70]
    assert np.std(roi_denoised) < np.std(roi_noisy)
    
    # Test edge preservation
    # Create edge mask using Sobel operators
    sobelx_noisy = cv2.Sobel(noisy_image, cv2.CV_64F, 1, 0, ksize=3)
    sobely_noisy = cv2.Sobel(noisy_image, cv2.CV_64F, 0, 1, ksize=3)
    edges_noisy = np.sqrt(sobelx_noisy**2 + sobely_noisy**2)
    
    sobelx_denoised = cv2.Sobel(denoised, cv2.CV_64F, 1, 0, ksize=3)
    sobely_denoised = cv2.Sobel(denoised, cv2.CV_64F, 0, 1, ksize=3)
    edges_denoised = np.sqrt(sobelx_denoised**2 + sobely_denoised**2)
    
    # Strong edges should be preserved
    strong_edges = edges_noisy > np.percentile(edges_noisy, 90)
    edge_retention = np.mean(edges_denoised[strong_edges]) / np.mean(edges_noisy[strong_edges])
    assert edge_retention > 0.7  # At least 70% edge strength retained
    
    # Test detail preservation in text-like regions
    # Text regions typically have high local variance
    local_std_noisy = cv2.blur((noisy_image - cv2.blur(noisy_image, (15,15)))**2, (15,15))
    local_std_denoised = cv2.blur((denoised - cv2.blur(denoised, (15,15)))**2, (15,15))
    
    # High detail regions
    detail_mask = local_std_noisy > np.percentile(local_std_noisy, 75)
    detail_retention = np.mean(local_std_denoised[detail_mask]) / np.mean(local_std_noisy[detail_mask])
    assert detail_retention > 0.6  # At least 60% detail preserved in high-detail regions

@pytest.mark.unit
def test_preprocess_image_complete(sample_image):
    """Test complete preprocessing pipeline optimized for text extraction."""
    processed = opencv_utils.preprocess_image(sample_image)
    
    # Basic checks
    assert len(processed.shape) == 2  # Should be grayscale
    assert isinstance(processed, np.ndarray)
    assert processed.dtype == np.uint8
    
    # Check image statistics are in expected ranges for OCR
    mean_val = np.mean(processed)
    std_val = np.std(processed)
    assert 115 <= mean_val <= 140  # Should be close to target mean of 127
    assert 35 <= std_val <= 45     # Should be close to target std of 40
    
    # Test edge preservation for text
    edges = cv2.Canny(processed, 100, 200)
    edge_pixels = np.count_nonzero(edges)
    assert edge_pixels > 0  # Should have detected edges
    
    # Test noise levels in uniform regions
    # Get the most uniform region using local standard deviation
    local_std = cv2.blur((processed - cv2.blur(processed, (5,5)))**2, (5,5))
    uniform_mask = local_std < np.percentile(local_std, 10)  # Bottom 10% most uniform regions
    if np.any(uniform_mask):
        uniform_region_std = np.std(processed[uniform_mask])
        assert uniform_region_std < 15  # Low noise in uniform regions

@pytest.mark.unit
def test_normalize_image(sample_image):
    """Test image normalization."""
    gray = opencv_utils.convert_to_grayscale(sample_image)
    normalized = opencv_utils.normalize_image(gray, target_mean=127, target_std=50)
    
    assert abs(np.mean(normalized) - 127) < 1.0  # Allow small deviation
    assert abs(np.std(normalized) - 50) < 1.0

@pytest.mark.unit
def test_extract_text_regions(sample_image):
    """Test text region extraction."""
    # Convert to binary image
    gray = opencv_utils.convert_to_grayscale(sample_image)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    regions = opencv_utils.extract_text_regions(binary)
    assert len(regions) > 0
    assert all(len(region) == 4 for region in regions)  # Each region should be (x,y,w,h)

@pytest.mark.unit
def test_error_handling():
    """Test error handling in utility functions."""
    invalid_image = np.zeros((10, 10), dtype=np.float32)  # Wrong data type
    
    # Each function should handle errors gracefully
    result = opencv_utils.enhance_contrast(invalid_image)
    assert isinstance(result, np.ndarray)
    
    result = opencv_utils.denoise_image(invalid_image)
    assert isinstance(result, np.ndarray)
    
    result = opencv_utils.normalize_image(invalid_image)
    assert isinstance(result, np.ndarray)
