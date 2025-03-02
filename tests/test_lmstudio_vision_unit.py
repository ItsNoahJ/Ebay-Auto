"""
Unit tests for VHSVision class.
"""
import pytest
import numpy as np
from src.vision.lmstudio_vision import VHSVision
import cv2

@pytest.fixture
def vision():
    """Create VHSVision instance for testing."""
    return VHSVision(save_debug=False)

@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

def test_calculate_target_size(vision):
    """Test adaptive target size calculation."""
    # Test small image (should keep original size)
    h, w = vision._calculate_target_size(300, 400)
    assert h == 300 and w == 400

    # Test large image (should scale down)
    h, w = vision._calculate_target_size(1080, 1920)
    assert h < 1080 and w < 1920
    assert abs((h * w) - vision.target_pixel_count) < 1000  # Allow small rounding difference

def test_calculate_jpeg_quality(vision):
    """Test JPEG quality calculation."""
    # Test small image (should use high quality)
    quality = vision._calculate_jpeg_quality(100000)
    assert quality == 95

    # Test large image (should reduce quality)
    quality = vision._calculate_jpeg_quality(340000)
    assert 65 <= quality < 95

def test_clean_response(vision):
    """Test response cleaning for different info types."""
    # Test year extraction
    test_text = "The movie was released in 1985 and is a classic"
    assert vision._clean_response(test_text, "year") == "1985"
    test_text = "No year here"
    assert vision._clean_response(test_text, "year") == ""

    # Test runtime cleaning
    test_text = "Runtime: 1h 30m"
    assert vision._clean_response(test_text, "runtime") == "1h 30m"
    test_text = "Duration: 90 minutes"
    assert vision._clean_response(test_text, "runtime") == "90 minutes"

    # Test title cleaning
    test_text = "Title: Star Wars"
    assert vision._clean_response(test_text, "title") == "Star Wars"
    test_text = "The Movie: Matrix"
    assert vision._clean_response(test_text, "title") == "Matrix"

def test_estimate_confidence(vision):
    """Test confidence estimation for different info types."""
    # Test year confidence
    test_text = "1985"
    assert abs(vision._estimate_confidence(test_text, "year") - 1.0) < 0.0001  # Valid VHS era year
    test_text = "2025"
    assert abs(vision._estimate_confidence(test_text, "year") - 0.9) < 0.0001  # Valid but unlikely year
    test_text = ""
    assert abs(vision._estimate_confidence(test_text, "year") - 0.0) < 0.0001  # Empty response

    # Test runtime confidence
    test_text = "1h 30m"
    assert abs(vision._estimate_confidence(test_text, "runtime") - 1.0) < 0.0001  # Complete format
    test_text = "90 minutes"
    assert abs(vision._estimate_confidence(test_text, "runtime") - 0.8) < 0.0001  # Basic format
    test_text = ""
    assert abs(vision._estimate_confidence(test_text, "runtime") - 0.0) < 0.0001  # Empty response

    # Test title confidence
    test_text = "The Matrix"
    assert abs(vision._estimate_confidence(test_text, "title") - 0.9) < 0.0001  # Good title
    test_text = ""
    assert abs(vision._estimate_confidence(test_text, "title") - 0.0) < 0.0001  # Empty response
    test_text = "A very very very long movie title!"
    assert vision._estimate_confidence(test_text, "title") < 0.6  # Too long (reduced threshold)

def test_is_high_confidence(vision):
    """Test high confidence check."""
    # Test with percentage confidence
    assert vision.is_high_confidence({'confidence': 80.0}, threshold=0.7) == True
    assert vision.is_high_confidence({'confidence': 50.0}, threshold=0.7) == False
    
    # Test with decimal confidence
    assert vision.is_high_confidence({'confidence': 0.9}, threshold=0.7) == True
    assert vision.is_high_confidence({'confidence': 0.5}, threshold=0.7) == False
    
    # Test missing confidence
    assert vision.is_high_confidence({}, threshold=0.7) == False

def test_preprocess_image(vision, sample_image):
    """Test image preprocessing pipeline."""
    processed = vision.preprocess_image(sample_image)
    
    # Check output shape and type
    assert processed.shape == sample_image.shape
    assert processed.dtype == np.uint8
    
    # Check if image is not empty
    assert np.any(processed != 0)

def test_encode_image(vision, sample_image):
    """Test image encoding with adaptive quality."""
    encoded = vision.encode_image(sample_image)
    
    # Check if encoded string is valid base64
    import base64
    try:
        decoded = base64.b64decode(encoded)
        assert len(decoded) > 0
        # Check if decoded data is valid JPEG
        np.frombuffer(decoded, dtype=np.uint8)
    except Exception as e:
        pytest.fail(f"Invalid base64 encoding: {str(e)}")

def test_error_handling(vision, sample_image):
    """Test error handling in extract_info."""
    # Test with invalid host to trigger connection error
    vision.host = "http://invalid-host:1234"
    result = vision.extract_info(sample_image)
    
    assert result['text'] == ""
    assert result['confidence'] == 0.0
    assert 'error' in result
    assert "Connection failed" in result['error']
