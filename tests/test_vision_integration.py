"""
Vision integration tests with timeout handling.
"""
import time
import pytest
from unittest.mock import patch, MagicMock

from src.vision.vhs_vision import VHSVision, TimeoutError
from src.vision.processor import VisionProcessor
from src.models.coordinator import ProcessingCoordinator
from tests.mocks import create_test_image

def test_vision_timeout_handling():
    """Test that vision processing properly handles timeouts."""
    # Create test objects
    vision = VHSVision(save_debug=False)
    processor = VisionProcessor(save_debug=False)
    coordinator = ProcessingCoordinator()
    
    # Create a test image
    test_image = create_test_image()
    
    # Test timeout in direct vision call
    with pytest.raises(TimeoutError):
        vision.extract_info(test_image, "title", timeout=1)
        
    # Test timeout propagation through processor
    with pytest.raises(TimeoutError):
        processor.process_image(test_image, timeout=1)
        
    # Test timeout handling in coordinator
    results = coordinator.process_tape(test_image, debug=False, api_timeout=1)
    assert not results["success"]
    assert "timeout" in results["error"].lower()
    assert results.get("error_type") == "timeout"
    
def test_stage_completion_tracking():
    """Test that stage completion is properly tracked."""
    coordinator = ProcessingCoordinator()
    progress_updates = {}
    
    def track_progress(stage: str, progress: float):
        progress_updates[stage] = progress
        
    # Process test image
    test_image = create_test_image()
    results = coordinator.process_tape(
        test_image,
        debug=False,
        progress_callback=track_progress
    )
    
    # Verify stages were tracked
    assert "grayscale_complete" in results
    assert "resize_complete" in results
    assert "enhance_complete" in results
    assert "denoise_complete" in results
    assert "text_complete" in results
    
    # Verify progress was tracked
    assert "grayscale" in progress_updates
    assert "resize" in progress_updates
    assert "enhance" in progress_updates
    assert "denoise" in progress_updates
    assert "text" in progress_updates
    
def test_partial_completion_on_timeout():
    """Test that completed stages are preserved on timeout."""
    coordinator = ProcessingCoordinator()
    progress_updates = {}
    completed_stages = set()
    
    def track_progress(stage: str, progress: float):
        progress_updates[stage] = progress
        if progress == 1.0:
            completed_stages.add(stage)
            
    # Process with short timeout
    test_image = create_test_image()
    results = coordinator.process_tape(
        test_image,
        debug=False,
        progress_callback=track_progress,
        api_timeout=1
    )
    
    # Verify early stages completed
    assert not results["success"]
    assert results.get("error_type") == "timeout"
    
    # Early stages should be marked complete
    for stage in ["grayscale", "resize", "enhance", "denoise"]:
        stage_key = f"{stage}_complete"
        if stage_key in results:
            assert results[stage_key] == (stage in completed_stages)
    
    # Text stage should not be complete
    assert not results.get("text_complete", False)
