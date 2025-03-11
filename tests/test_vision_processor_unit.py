"""
Unit tests for VisionProcessor preprocessing image functionality.
"""
import numpy as np
from unittest.mock import Mock, patch
import pytest

from src.vision.processor import VisionProcessor
from src.models.coordinator import ProcessingCoordinator

@pytest.fixture(autouse=True)
def mock_vision_init():
    """Mock VHSVision initialization."""
    with patch('src.vision.processor.VHSVision') as mock_vision:
        # Create a basic mock instance
        mock_instance = Mock()
        mock_instance.check_models = Mock(return_value=True)
        mock_instance.available_models = ["model1", "model2"]
        mock_instance.extract_text = Mock(return_value={
            "success": True,
            "text": "Sample text",
            "confidence": 0.9
        })
        mock_vision.return_value = mock_instance
        yield mock_vision

@pytest.fixture
def processor():
    """Create a VisionProcessor instance for testing."""
    return VisionProcessor(save_debug=True)

def test_vision_processor_store_preprocessing_images(processor):
    """Test storing preprocessing stage images."""
    # Create test image
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Store test images
    processor.preprocessing_images = {
        "Original": test_image.copy(),
        "Grayscale": test_image.copy(),
        "Enhanced": test_image.copy(),
        "Denoised": test_image.copy(),
        "Text Detection": test_image.copy()
    }
    
    # Verify images are stored
    for stage in ["Original", "Grayscale", "Enhanced", "Denoised", "Text Detection"]:
        image = processor.get_preprocessing_image(stage)
        assert image is not None
        assert image.shape == (100, 100, 3)

def test_vision_processor_clear_preprocessing_images(processor):
    """Test clearing preprocessing stage images."""
    # Create and store test image
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    processor.preprocessing_images = {
        "Original": test_image.copy()
    }
    
    # Clear images
    processor.preprocessing_images.clear()
    
    # Verify images are cleared
    assert processor.get_preprocessing_image("Original") is None

@pytest.mark.parametrize("stage_name", [
    "Original",
    "Grayscale",
    "Enhanced",
    "Denoised",
    "Text Detection"
])
def test_vision_processor_get_nonexistent_image(processor, stage_name):
    """Test getting preprocessing image that doesn't exist."""
    assert processor.get_preprocessing_image(stage_name) is None

@pytest.mark.parametrize("invalid_value", [
    "not an image",
    123,
    None,
    [],
    {},
])
def test_vision_processor_store_invalid_image(processor, invalid_value):
    """Test storing invalid image type."""
    with pytest.raises((TypeError, ValueError)):
        # Try to store an invalid value
        processor.store_preprocessing_image("Invalid", invalid_value)
        # Try to access the invalid value
        processor.get_preprocessing_image("Invalid")

def test_vision_processor_store_none_image(processor):
    """Test storing None as image value."""
    with pytest.raises(ValueError):
        processor.store_preprocessing_image("Stage", None)

def test_vision_processor_store_wrong_shape(processor):
    """Test storing image with wrong shape."""
    # Create 2D array instead of 3D
    invalid_image = np.zeros((100, 100), dtype=np.uint8)
    with pytest.raises(ValueError):
        processor.store_preprocessing_image("Stage", invalid_image)
