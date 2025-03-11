"""
Unit tests for ProcessingCoordinator image conversion functionality.
"""
import numpy as np
from unittest.mock import Mock, patch, PropertyMock
import pytest
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

from src.models.coordinator import ProcessingCoordinator
from src.vision.processor import VisionProcessor

@pytest.fixture
def mock_vision_processor():
    """Mock VisionProcessor."""
    with patch('src.models.coordinator.VisionProcessor') as mock:
        processor = Mock(spec=VisionProcessor)
        processor.preprocessing_images = {}
        processor.extract_text.return_value = {
            "success": True,
            "vision_data": {
                "text": "Sample text",
                "confidence": 0.9
            }
        }
        mock.return_value = processor
        yield processor

@pytest.fixture
def test_image():
    """Create a test image."""
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[30:70, 30:70] = 255  # Add white square
    return image

@pytest.fixture
def coordinator(mock_vision_processor, qapp):
    """Create ProcessingCoordinator instance for testing."""
    coord = ProcessingCoordinator()
    # Set the mock processor directly
    coord.processor = mock_vision_processor
    return coord

def test_coordinator_convert_cv_to_qt(coordinator, test_image, qapp):
    """Test OpenCV to Qt image conversion."""
    # Convert image
    pixmap = coordinator._convert_cv_to_qt(test_image)
    
    # Verify conversion
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()
    assert pixmap.width() == 100
    assert pixmap.height() == 100

def test_coordinator_get_preprocessing_images(coordinator, test_image, qapp):
    """Test getting preprocessing images as Qt pixmaps."""
    # Store test images
    coordinator.current_preprocessing_images = {
        "Original": test_image.copy(),
        "Grayscale": test_image.copy(),
        "Enhanced": test_image.copy(),
        "Denoised": test_image.copy(),
        "Text Detection": test_image.copy()
    }
    
    # Get Qt pixmaps
    pixmaps = coordinator.get_preprocessing_images()
    
    # Verify pixmaps
    assert len(pixmaps) == 5
    for stage, pixmap in pixmaps.items():
        assert isinstance(pixmap, QPixmap)
        assert not pixmap.isNull()
        assert pixmap.width() == 100
        assert pixmap.height() == 100

def test_coordinator_empty_preprocessing_images(coordinator, qapp):
    """Test getting preprocessing images when none exist."""
    # Get Qt pixmaps
    pixmaps = coordinator.get_preprocessing_images()
    
    # Verify empty result
    assert len(pixmaps) == 0

def test_coordinator_process_tape_with_image(coordinator, test_image, qapp):
    """Test processing tape with a valid image."""
    # Setup preprocessing images
    coordinator.processor.preprocessing_images = {
        "Original": test_image.copy(),
        "Enhanced": test_image.copy()
    }
    
    # Process image
    result = coordinator.process_tape(test_image)
    
    # Verify result
    assert result["success"] is True
    assert isinstance(result["vision_data"], dict)
    
    # Verify preprocessing images were copied
    assert len(coordinator.current_preprocessing_images) == 2
    assert "Original" in coordinator.current_preprocessing_images
    assert "Enhanced" in coordinator.current_preprocessing_images
    
    # Verify images are numpy arrays
    for image in coordinator.current_preprocessing_images.values():
        assert isinstance(image, np.ndarray)
        assert image.shape == (100, 100, 3)
