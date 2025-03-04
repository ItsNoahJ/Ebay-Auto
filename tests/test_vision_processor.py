"""
Unit tests for vision processing module.
"""
import pytest
import cv2
import numpy as np
from unittest.mock import Mock, call

from src.vision.processor import VisionProcessor

@pytest.fixture
def processor():
    """Create a VisionProcessor instance for testing."""
    return VisionProcessor(save_debug=False)

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

@pytest.mark.unit
def test_process_image_progress_tracking(processor, sample_vhs_image):
    """Test that process_image correctly reports progress through callbacks."""
    progress_callback = Mock()
    
    results = processor.process_image(sample_vhs_image, progress_callback=progress_callback)
    
    # Verify callback was called for each stage
    expected_calls = [
        # Initial grayscale progress
        call("grayscale", 0.0),
        call("grayscale", 0.5),
        call("grayscale", 1.0),
        
        # Resize progress
        call("resize", 0.0),
        call("resize", 1.0),
        
        # Enhancement progress
        call("enhance", 0.0),
        call("enhance", 1.0),
        
        # Denoising progress
        call("denoise", 0.0),
        call("denoise", 1.0),
        
        # Text extraction progress (multiple updates as categories are processed)
        call("text", 0.0),
    ]
    
    # The text extraction will have additional calls as categories are processed
    # Just verify the key stages were called in order
    actual_calls = progress_callback.call_args_list
    
    # Check that all expected calls are present in order
    for expected, actual in zip(expected_calls, actual_calls):
        assert expected == actual, f"Expected {expected}, got {actual}"
    
    # Verify we got a final text progress of 1.0
    assert call("text", 1.0) in actual_calls
    
    # Verify the results contain expected fields
    assert isinstance(results, dict)
    assert "confidence" in results
    assert "extracted_data" in results
    assert isinstance(results.get("confidence", {}), dict)

@pytest.mark.unit
def test_process_image_handles_missing_callback(processor, sample_vhs_image):
    """Test that process_image works without a progress callback."""
    results = processor.process_image(sample_vhs_image)  # No callback
    assert isinstance(results, dict)
    assert "confidence" in results

@pytest.mark.unit
def test_process_image_error_handling(processor):
    """Test error handling in process_image."""
    progress_callback = Mock()
    
    # Try to process a non-existent image
    results = processor.process_image(
        "nonexistent.jpg",
        progress_callback=progress_callback
    )
    
    assert "error" in results
    assert not results.get("success", False)
    
    # Verify callback was still called with initial stage
    progress_callback.assert_called_with("grayscale", 0.0)

@pytest.mark.unit
def test_process_image_with_invalid_image(processor, tmp_path):
    """Test handling of invalid/corrupt image files."""
    # Create an invalid image file
    invalid_path = tmp_path / "invalid.jpg"
    with open(invalid_path, "w") as f:
        f.write("not an image")
    
    progress_callback = Mock()
    results = processor.process_image(str(invalid_path), progress_callback=progress_callback)
    
    assert "error" in results
    assert not results.get("success", False)
    
    # Should still get initial progress call
    progress_callback.assert_called_with("grayscale", 0.0)

@pytest.mark.unit
def test_process_image_success_validation(processor, sample_vhs_image):
    """Test successful processing includes all required fields."""
    results = processor.process_image(sample_vhs_image)
    
    assert results.get("success", False)
    assert isinstance(results.get("confidence", {}), dict)
    assert isinstance(results.get("extracted_data", {}), dict)
    assert isinstance(results.get("source", {}), dict)
    
    # Check that confidence scores are normalized
    for score in results.get("confidence", {}).values():
        assert 0.0 <= score <= 1.0, "Confidence scores should be normalized"

@pytest.mark.unit
def test_api_backup_triggering(processor, sample_vhs_image, monkeypatch):
    """Test that API backup is triggered for low confidence results."""
    # Mock the _needs_api_backup method to always return True
    monkeypatch.setattr(processor, "_needs_api_backup", lambda x: True)
    
    # Create a mock for the API call
    mock_api_result = {
        "title": "API Title",
        "year": "2024",
        "runtime": "120",
        "confidence": 0.85
    }
    monkeypatch.setattr(
        "src.enrichment.api_client.search_movie_details",
        lambda x: mock_api_result
    )
    
    results = processor.process_image(sample_vhs_image)
    
    # Verify that API data was used
    assert any(source == "api" for source in results.get("source", {}).values())
