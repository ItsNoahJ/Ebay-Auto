"""
Integration tests to verify interoperability between components.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, PropertyMock, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPixmap

from src.gui.results_view import ResultsView
from src.models.coordinator import ProcessingCoordinator
from src.vision.processor import VisionProcessor

@pytest.fixture
def test_vhs_image():
    """Create a test VHS cover image."""
    image = np.zeros((300, 200, 3), dtype=np.uint8)
    # Add some text-like features
    image[50:70, 30:170] = 255  # Title area
    image[100:110, 30:100] = 255  # Year area
    return image

@pytest.fixture
def mock_vhs_vision():
    """Create a mock VHSVision instance."""
    mock = MagicMock()
    mock.check_models.return_value = True
    mock.extract_text.return_value = {
        'success': True,
        'vision_data': {
            'title': "Test Movie",
            'year': "1995",
            'runtime': "120 min",
            'confidence': {
                'title': 0.95,
                'year': 0.90,
                'runtime': 0.85
            }
        }
    }
    # Mock preprocessing images as a property
    type(mock).preprocessing_images = PropertyMock(return_value={
        "Grayscale": np.zeros((100, 100, 3), dtype=np.uint8),
        "Enhanced": np.zeros((100, 100, 3), dtype=np.uint8)
    })
    return mock

@pytest.fixture
def coordinator(mock_vhs_vision):
    """Create ProcessingCoordinator with mocked vision."""
    with patch('src.vision.processor.VHSVision', return_value=mock_vhs_vision):
        coord = ProcessingCoordinator()
        # Mock the vision property directly
        coord.processor.vision = mock_vhs_vision
        return coord

@pytest.fixture
def results_view(qapp):
    """Create ResultsView instance."""
    widget = ResultsView()
    widget.setup_ui()
    return widget

def test_end_to_end_processing(test_vhs_image, coordinator, results_view):
    """Test complete workflow from image input to GUI display."""
    # Process image through coordinator
    result = coordinator.process_tape(test_vhs_image)
    
    # Verify coordinator results
    assert isinstance(result, dict)
    assert result.get("success") is True
    assert "vision_data" in result
    vision_data = result["vision_data"]
    assert vision_data["title"] == "Test Movie"
    assert vision_data["year"] == "1995"
    
    # Verify preprocessing images were generated
    preprocessing_images = coordinator.get_preprocessing_images()
    assert len(preprocessing_images) > 0
    assert "Original" in preprocessing_images
    assert "Enhanced" in preprocessing_images
    
    # Update GUI with results
    results_view.update_results(result)
    
    # Verify text display
    displayed_text = results_view.text_edit.toPlainText()
    assert "Test Movie" in displayed_text
    assert "1995" in displayed_text
    
    # Update GUI with preprocessing images
    for stage, pixmap in preprocessing_images.items():
        results_view.update_preprocessing_image(stage, pixmap)
        
    # Verify preprocessing images in GUI
    for stage in preprocessing_images.keys():
        assert results_view.get_stage_image(stage) is not None
        
    # Verify confidence visualization
    assert results_view.confidence_bars["title"].value() == 95

def test_error_handling_integration(test_vhs_image, coordinator, mock_vhs_vision, results_view):
    """Test error handling across components."""
    # Ensure clean state
    results_view.clear()
    
    # Simulate vision API error
    mock_vhs_vision.extract_text.return_value = {
        'success': False,
        'error': "API Connection Error",
        'vision_data': {}  # Empty vision data on error
    }
    
    # Process image
    result = coordinator.process_tape(test_vhs_image)
    
    # Verify error propagation
    assert isinstance(result, dict)
    assert result.get("success") is False
    assert "error" in result
    
    # Update GUI with error result
    results_view.update_results(result)
    
    # Verify error display
    assert "Error" in results_view.text_edit.toPlainText()
    assert "API Connection Error" in results_view.text_edit.toPlainText()
    
    # Verify confidence bars are reset to zero
    for bar in results_view.confidence_bars.values():
        # Get current value before assertion
        value = bar.value()
        assert value == 0, f"Expected confidence bar value to be 0, got {value}"

def test_preprocessing_pipeline_integration(test_vhs_image, coordinator):
    """Test preprocessing pipeline consistency."""
    # Get preprocessing steps
    result = coordinator.process_tape(test_vhs_image)
    images = coordinator.get_preprocessing_images()
    
    # Verify image progression
    assert "Original" in images
    assert "Grayscale" in images
    assert "Enhanced" in images
    assert images["Enhanced"].width() > 0  # Valid image output
    
    # Verify image type consistency
    for stage, image in images.items():
        assert isinstance(image, QPixmap)
        assert not image.isNull()

def test_state_cleanup_integration(test_vhs_image, coordinator, results_view):
    """Test proper cleanup between processing runs."""
    # First run
    result1 = coordinator.process_tape(test_vhs_image)
    results_view.update_results(result1)
    
    # Store initial state
    first_text = results_view.text_edit.toPlainText()
    first_images = results_view.preprocessing_images.copy()
    
    # Clear everything
    coordinator.clear()
    results_view.clear()
    
    # Verify clean state
    assert not results_view.text_edit.toPlainText()
    assert not results_view.preprocessing_images
    assert not coordinator.get_preprocessing_images()
    
    # Second run
    result2 = coordinator.process_tape(test_vhs_image)
    results_view.update_results(result2)
    
    # Verify fresh state
    assert results_view.text_edit.toPlainText() == first_text
    assert len(results_view.preprocessing_images) == len(first_images)
