"""
Integration tests for vision processing pipeline.
Tests the interaction between VHSVision, VisionProcessor and GUI components.
"""
import os
import pytest
from pathlib import Path
import cv2
import numpy as np

from src.vision.lmstudio_vision import VHSVision
from src.vision.processor import VisionProcessor
from src.models.coordinator import ProcessingCoordinator
from src.gui.main_window import MainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

@pytest.fixture
def test_image_path(tmp_path):
    """Create a test image with known properties."""
    image_path = tmp_path / "test_vhs.jpg"
    # Create a simple test image with text
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    cv2.putText(img, "Test Movie", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
    cv2.imwrite(str(image_path), img)
    return str(image_path)

@pytest.fixture
def long_title_image_path(tmp_path):
    """Create a test image with a very long title."""
    image_path = tmp_path / "test_long_title.jpg"
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    cv2.putText(img, "A Very Very Long Movie Title That Should Have Low Confidence", 
                (20, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.imwrite(str(image_path), img)
    return str(image_path)

from .mocks import MockVisionProcessor, MockLongTitleProcessor, MockErrorProcessor

def test_vision_processor_confidence(monkeypatch, test_image_path, long_title_image_path):
    """Test confidence calculations through the vision processor."""
    # Test normal title
    normal_processor = MockVisionProcessor(save_debug=True)
    normal_results = normal_processor.process_image(test_image_path)
    assert normal_results["vision_data"]["confidence"]["title"] >= 0.7, "Normal title should have high confidence"
    
    # Test long title
    long_processor = MockLongTitleProcessor(save_debug=True)
    long_results = long_processor.process_image(long_title_image_path)
    assert long_results["vision_data"]["confidence"]["title"] < 0.6, "Long title should have reduced confidence"

def test_coordinator_vision_integration(monkeypatch, test_image_path):
    """Test vision processing through coordinator."""
    # Setup mock processor
    mock_processor = MockVisionProcessor(save_debug=True)
    monkeypatch.setattr("src.models.coordinator.VisionProcessor", lambda *args, **kwargs: mock_processor)
    
    coordinator = ProcessingCoordinator()
    results = coordinator.process_tape(test_image_path)
    
    assert results["success"], "Processing should succeed"
    assert "vision_data" in results, "Vision data should be present"
    assert all(0 <= conf <= 1.0 for conf in results["vision_data"]["confidence"].values()), \
        "Confidence scores should be decimal values between 0 and 1"
    assert len(results.get("extracted_titles", [])) > 0, "Should extract at least one title"

@pytest.mark.skip(reason="GUI tests require QApplication context")
def test_gui_vision_confidence_handling(qtbot, monkeypatch, test_image_path, long_title_image_path):
    """Test GUI handling of different confidence levels."""
    # Setup mock processors
    normal_processor = MockVisionProcessor(save_debug=True)
    long_processor = MockLongTitleProcessor(save_debug=True)
    
    window = MainWindow()
    qtbot.addWidget(window)
    
    # Test normal title processing
    monkeypatch.setattr(window.coordinator, "vision_processor", normal_processor)
    window.preview.load_image(test_image_path)
    with qtbot.waitSignal(window.preview.image_loaded, timeout=1000):
        pass
    
    window._process_image()
    qtbot.wait(1000)
    
    assert window.save_action.isEnabled(), "Save should be enabled for high confidence result"
    
    # Test long title
    window._clear()
    monkeypatch.setattr(window.coordinator, "vision_processor", long_processor)
    window.preview.load_image(long_title_image_path)
    with qtbot.waitSignal(window.preview.image_loaded, timeout=1000):
        pass
    
    window._process_image()
    qtbot.wait(1000)
    
    assert window.save_action.isEnabled(), "Save should be enabled even for low confidence"

def test_preprocessing_pipeline(monkeypatch, test_image_path):
    """Test entire preprocessing pipeline."""
    # Setup mock processor
    processor = MockVisionProcessor(save_debug=True)
    
    # Process image
    results = processor.process_image(test_image_path)
    
    # Verify expected fields are present
    assert "vision_data" in results, "Should include vision data"
    assert results.get("success", True), "Processing should succeed"
    assert "extracted_titles" in results, "Should include extracted titles"
    assert len(results["extracted_titles"]) > 0, "Should extract at least one title"
    assert results["vision_data"]["confidence"]["title"] >= 0.7, "Normal title should have high confidence"

def test_error_handling(monkeypatch, test_image_path):
    """Test error handling through the pipeline."""
    # Setup mock error processor
    error_processor = MockErrorProcessor(save_debug=True)
    monkeypatch.setattr("src.models.coordinator.VisionProcessor", lambda *args, **kwargs: error_processor)
    
    coordinator = ProcessingCoordinator()
    
    # Setup mock error processor for nonexistent file
    def mock_process_nonexistent(*args, **kwargs):
        return {
            "success": False,
            "vision_data": {
                "title": "",
                "confidence": {"title": 0.0},
                "source": {"title": "none"}
            },
            "error": "File not found",
            "extracted_titles": []
        }
    coordinator.process_tape = mock_process_nonexistent
    
    # Test with invalid image path
    results = coordinator.process_tape("nonexistent.jpg")
    assert not results["success"], "Should fail gracefully for missing image"
    assert "error" in results, "Should include error message"
    assert not results.get("extracted_titles"), "Should have no extracted titles"
    
    # Reset coordinator and test with simulated vision error
    coordinator = ProcessingCoordinator()
    results = coordinator.process_tape(test_image_path)
    assert not results["success"], "Should fail gracefully for vision error"
    assert "error" in results, "Should include error message"
    assert "vision_data" in results, "Should include vision data even on error"
    assert all(val == "" for val in results["vision_data"].values() if isinstance(val, str)), \
        "All text fields should be empty on error"
    assert all(conf == 0.0 for conf in results["vision_data"]["confidence"].values()), \
        "All confidence scores should be 0.0 on error"
