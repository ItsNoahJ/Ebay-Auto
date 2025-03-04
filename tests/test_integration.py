"""
Integration tests for the complete image processing pipeline.
"""
import os
import time
from pathlib import Path

import cv2
import numpy as np
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.models.coordinator import ProcessingCoordinator
from src.vision.processor import VisionProcessor
from src.gui.widgets import ProcessingStatusWidget
from src.utils import opencv_utils

@pytest.fixture
def sample_vhs_files(tmp_path):
    """Create multiple sample VHS cover images for testing."""
    images = []
    
    # Create several test images with varying content
    for i in range(3):
        image = np.zeros((300, 200, 3), dtype=np.uint8)
        
        # Add different text for each image
        cv2.rectangle(image, (20, 20), (180, 60), (255, 255, 255), -1)
        cv2.putText(image, f"TEST TITLE {i+1}", (30, 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Save the image
        image_path = tmp_path / f"test_vhs_{i+1}.jpg"
        cv2.imwrite(str(image_path), image)
        images.append(str(image_path))
    
    return images

@pytest.mark.integration
def test_full_pipeline_integration(sample_vhs_files, qtbot, monkeypatch, tmp_path):
    """Test the complete processing pipeline from GUI to results."""
    # Set up test environment
    monkeypatch.setattr(
        "src.config.settings.STORAGE_PATHS",
        {"results": tmp_path / "results"}
    )
    
    # Create main window
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Get references to key components
    status_widget = window.findChild(ProcessingStatusWidget)
    assert status_widget is not None
    
    # Process each test image
    for image_path in sample_vhs_files:
        # Load image
        qtbot.mouseClick(window.load_button, Qt.MouseButton.LeftButton)
        window.image_path = image_path  # Simulate file selection
        
        # Start processing
        qtbot.mouseClick(window.process_button, Qt.MouseButton.LeftButton)
        
        # Wait for processing to complete (timeout after 30 seconds)
        start_time = time.time()
        while not window.processing_complete and time.time() - start_time < 30:
            QApplication.processEvents()
            time.sleep(0.1)
        
        assert window.processing_complete
        
        # Verify progress tracking
        for stage_data in status_widget.stage_bars.values():
            progress_bar = stage_data["progress"]
            percent_label = stage_data["percent"]
            assert progress_bar.value() == 100
            assert percent_label.text() == "100%"
        
        # Verify results
        assert window.results is not None
        assert window.results["success"]
        assert len(window.results["extracted_titles"]) > 0
        
        # Check that results were saved
        results_file = Path(window.results["results_path"])
        assert results_file.exists()
        
        # Reset for next image
        qtbot.mouseClick(window.clear_button, Qt.MouseButton.LeftButton)
        assert status_widget.time_label.text() == "00:00"

@pytest.mark.integration
def test_pipeline_error_handling(tmp_path, qtbot):
    """Test error handling throughout the pipeline."""
    # Create an invalid image file
    invalid_path = tmp_path / "invalid.jpg"
    with open(invalid_path, "w") as f:
        f.write("not an image")
    
    # Initialize components
    coordinator = ProcessingCoordinator()
    widget = ProcessingStatusWidget()
    qtbot.addWidget(widget)
    
    # Start processing
    widget.start_processing()
    results = coordinator.process_tape(
        str(invalid_path),
        progress_callback=widget.update_stage
    )
    
    # Verify error handling
    assert not results["success"]
    assert "error" in results
    assert widget.status_label.text() == "Error"

@pytest.mark.integration
def test_preprocessing_stages(sample_vhs_files, qtbot):
    """Test each preprocessing stage's impact on image quality."""
    image_path = sample_vhs_files[0]
    
    # Load original image
    original = cv2.imread(image_path)
    assert original is not None
    
    # Test each preprocessing stage
    gray = opencv_utils.convert_to_grayscale(original)
    assert len(gray.shape) == 2
    
    resized = opencv_utils.resize_image(gray, target_width=1024)
    assert resized.shape[1] <= 1024
    
    enhanced = opencv_utils.enhance_contrast(resized)
    assert np.std(enhanced) > np.std(resized)  # Higher contrast
    
    denoised = opencv_utils.denoise_image(enhanced)
    center_roi = lambda img: img[img.shape[0]//4:3*img.shape[0]//4, 
                                img.shape[1]//4:3*img.shape[1]//4]
    assert np.std(center_roi(denoised)) < np.std(center_roi(enhanced))

@pytest.mark.integration
def test_memory_usage_tracking(sample_vhs_files, qtbot):
    """Test memory usage tracking during processing."""
    widget = ProcessingStatusWidget()
    qtbot.addWidget(widget)
    
    # Record initial memory
    initial_memory = float(widget.memory_label.text().split()[0])
    
    # Process large image
    coordinator = ProcessingCoordinator()
    widget.start_processing()
    coordinator.process_tape(
        sample_vhs_files[0],
        progress_callback=widget.update_stage
    )
    
    # Verify memory increased
    final_memory = float(widget.memory_label.text().split()[0])
    assert final_memory > initial_memory

@pytest.mark.integration
def test_concurrent_operations(sample_vhs_files, qtbot):
    """Test handling of concurrent processing attempts."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Start first processing
    window.image_path = sample_vhs_files[0]
    qtbot.mouseClick(window.process_button, Qt.MouseButton.LeftButton)
    
    # Verify second processing attempt is blocked
    assert not window.process_button.isEnabled()
    
    # Wait for completion
    while not window.processing_complete:
        QApplication.processEvents()
        time.sleep(0.1)
    
    # Verify processing is re-enabled
    assert window.process_button.isEnabled()
