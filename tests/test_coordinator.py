"""
Tests for media processing coordinator.
"""
import json
from pathlib import Path
from unittest.mock import Mock, patch, call

import cv2
import numpy as np
import pytest

from src.models.coordinator import ProcessingCoordinator
from src.vision.processor import VisionProcessor
from src.gui.widgets import ProcessingStatusWidget

@pytest.fixture
def coordinator():
    """Create a ProcessingCoordinator instance for testing."""
    return ProcessingCoordinator()

@pytest.fixture
def sample_vhs_image(tmp_path):
    """Create a sample VHS cover image for testing."""
    # Create a test image with some text-like features
    image = np.zeros((300, 200, 3), dtype=np.uint8)
    
    # Add a white rectangle for title area
    cv2.rectangle(image, (20, 20), (180, 60), (255, 255, 255), -1)
    # Add some simulated text
    cv2.putText(image, "TEST TITLE", (30, 45), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Save the image
    image_path = tmp_path / "test_vhs.jpg"
    cv2.imwrite(str(image_path), image)
    
    return str(image_path)

def test_process_tape_with_progress(coordinator, sample_vhs_image):
    """Test process_tape with progress tracking."""
    progress_callback = Mock()
    
    results = coordinator.process_tape(
        sample_vhs_image,
        progress_callback=progress_callback
    )
    
    # Verify callback was called for each stage
    expected_stages = ["grayscale", "resize", "enhance", "denoise", "text"]
    actual_stages = [call[0][0] for call in progress_callback.call_args_list]
    
    # Check that all expected stages were called
    for stage in expected_stages:
        assert stage in actual_stages
        
    # Each stage should have at least start (0.0) and end (1.0) progress
    for stage in expected_stages:
        stage_calls = [
            call for call in progress_callback.call_args_list 
            if call[0][0] == stage
        ]
        # Get progress values for this stage
        progress_values = [call[0][1] for call in stage_calls]
        
        assert 0.0 in progress_values, f"{stage} missing start progress"
        assert 1.0 in progress_values, f"{stage} missing end progress"
        
    # Verify results structure
    assert results["success"]
    assert "vision_data" in results
    assert isinstance(results["extracted_titles"], list)

def test_process_tape_without_callback(coordinator, sample_vhs_image):
    """Test process_tape works without a progress callback."""
    results = coordinator.process_tape(sample_vhs_image)
    assert results["success"]
    assert "vision_data" in results

def test_process_tape_nonexistent_image(coordinator):
    """Test processing a non-existent image."""
    progress_callback = Mock()
    
    results = coordinator.process_tape(
        "nonexistent.jpg",
        progress_callback=progress_callback
    )
    
    assert not results["success"]
    assert "error" in results
    progress_callback.assert_called_with("grayscale", 0.0)

def test_process_tape_invalid_image(coordinator, tmp_path):
    """Test processing an invalid image file."""
    # Create an invalid image file
    invalid_path = tmp_path / "invalid.jpg"
    with open(invalid_path, "w") as f:
        f.write("not an image")
    
    progress_callback = Mock()
    results = coordinator.process_tape(
        str(invalid_path),
        progress_callback=progress_callback
    )
    
    assert not results["success"]
    assert "error" in results
    progress_callback.assert_called_with("grayscale", 0.0)

@pytest.mark.integration
def test_coordinator_widget_integration(coordinator, sample_vhs_image, qtbot):
    """Test integration between coordinator and ProcessingStatusWidget."""
    # Create widget
    widget = ProcessingStatusWidget()
    qtbot.addWidget(widget)
    
    # Process image using widget's methods as callbacks
    def progress_callback(stage: str, progress: float):
        widget.update_stage(stage, progress)
    
    widget.start_processing()
    results = coordinator.process_tape(
        sample_vhs_image,
        progress_callback=progress_callback
    )
    
    # Verify widget state
    for stage_data in widget.stage_bars.values():
        progress_bar = stage_data["progress"]
        assert progress_bar.value() == 100  # All stages should complete
    
    assert results["success"]

def test_results_saving(coordinator, sample_vhs_image, tmp_path, monkeypatch):
    """Test that results are properly saved."""
    # Mock STORAGE_PATHS to use tmp_path
    monkeypatch.setattr(
        "src.config.settings.STORAGE_PATHS",
        {"results": tmp_path}
    )
    
    results = coordinator.process_tape(sample_vhs_image)
    
    # Verify results were saved
    assert results["results_path"]
    results_file = Path(results["results_path"])
    assert results_file.exists()
    
    # Verify saved JSON is valid
    with open(results_file) as f:
        saved_data = json.load(f)
        assert saved_data["success"]
        assert "vision_data" in saved_data

@pytest.mark.integration
def test_full_processing_pipeline(coordinator, sample_vhs_image, qtbot):
    """Test the full processing pipeline with UI updates."""
    # Create widget
    widget = ProcessingStatusWidget()
    qtbot.addWidget(widget)
    
    # Start processing
    widget.start_processing()
    
    # Process with progress updates
    results = coordinator.process_tape(
        sample_vhs_image,
        progress_callback=widget.update_stage
    )
    
    # Verify success
    assert results["success"]
    
    # Verify widget state
    assert widget.time_label.text() != "00:00"  # Time should have elapsed
    assert float(widget.memory_label.text().split()[0]) > 0  # Should show memory usage
    
    # All progress bars should be at 100%
    for stage_data in widget.stage_bars.values():
        assert stage_data["progress"].value() == 100
        assert stage_data["percent"].text() == "100%"
