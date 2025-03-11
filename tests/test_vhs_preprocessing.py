"""
Tests for VHS preprocessing pipeline with timeout handling.
"""
import pytest
import time
import numpy as np
from unittest.mock import MagicMock

from src.vision.preprocessing import (
    PreprocessingPipeline,
    FastCLAHE,
    BilateralFilter,
    RegionDetector,
    TimeoutError
)
from tests.mocks import create_test_image

def test_preprocessing_timeout():
    """Test timeout during preprocessing operations."""
    from tests.mocks import PreprocessorWithTimeout
    
    # Create pipeline with significant delay
    pipeline = PreprocessorWithTimeout(processing_delay=2)
    image = create_test_image()
    
    # Process with timeout shorter than delay
    with pytest.raises(TimeoutError):
        pipeline.preprocess(
            image,
            timeout=1  # 1s timeout vs 2s delay
        )

def test_preprocessing_progress_tracking():
    """Test progress callback during preprocessing."""
    pipeline = PreprocessingPipeline()
    image = create_test_image()
    
    # Track progress updates
    progress_updates = {}
    def track_progress(stage: str, progress: float):
        if stage not in progress_updates:
            progress_updates[stage] = []
        progress_updates[stage].append(progress)
    
    # Process image with progress tracking
    pipeline.preprocess(
        image,
        progress_callback=track_progress
    )
    
    # Verify progress tracking
    expected_stages = ["grayscale", "resize", "denoise", "enhance"]
    for stage in expected_stages:
        assert stage in progress_updates
        assert progress_updates[stage][-1] == 1.0  # Final progress should be 100%
        assert 0.0 in progress_updates[stage]  # Should start at 0%

def test_preprocessing_stages_order():
    """Test that preprocessing stages execute in correct order."""
    pipeline = PreprocessingPipeline()
    image = create_test_image()
    
    # Track stage execution order
    stage_order = []
    def track_progress(stage: str, progress: float):
        if progress == 0.0:  # Track when stage starts
            stage_order.append(stage)
    
    # Process image
    pipeline.preprocess(
        image,
        progress_callback=track_progress
    )
    
    # Verify stage order
    expected_order = ["grayscale", "resize", "denoise", "enhance"]
    assert stage_order == expected_order

def test_preprocessing_error_handling():
    """Test error handling during preprocessing."""
    pipeline = PreprocessingPipeline()
    
    # Create invalid input
    invalid_image = np.array([])  # Empty array
    
    # Track progress
    progress_updates = {}
    def track_progress(stage: str, progress: float):
        if stage not in progress_updates:
            progress_updates[stage] = []
        progress_updates[stage].append(progress)
    
    # Process invalid image
    result_image, regions = pipeline.preprocess(
        invalid_image,
        progress_callback=track_progress
    )
    
    # Verify error handling
    assert regions == []  # Should return empty regions list
    assert np.array_equal(result_image, invalid_image)  # Should return original image
    
    # Verify all stages marked as complete
    expected_stages = ["grayscale", "resize", "denoise", "enhance"]
    for stage in expected_stages:
        assert stage in progress_updates
        assert progress_updates[stage][-1] == 1.0

def test_preprocessing_with_region_detection():
    """Test full preprocessing pipeline with region detection."""
    pipeline = PreprocessingPipeline()
    image = create_test_image()
    
    # Process image
    processed, regions = pipeline.preprocess(image)
    
    # Verify preprocessing results
    assert processed is not None
    assert len(processed.shape) == 2  # Should be grayscale
    assert len(regions) > 0  # Should detect some regions
    
    # Verify region properties
    for region in regions:
        assert region.width > 0
        assert region.height > 0
        assert region.image is not None
        assert region.image.size > 0

def test_preprocessing_partial_completion():
    """Test partial completion before timeout."""
    pipeline = PreprocessingPipeline()
    image = create_test_image()
    
    # Track progress
    progress_updates = {}
    def track_progress(stage: str, progress: float):
        if stage not in progress_updates:
            progress_updates[stage] = []
        progress_updates[stage].append(progress)
    
    # Process with short timeout
    try:
            # Add small sleep to ensure we get to enhancement stage
            time.sleep(0.1)
            pipeline.preprocess(
                image,
                progress_callback=track_progress,
                timeout=0.2  # Allow time to start enhancement
            )
    except TimeoutError:
        # Verify early stages completed
        assert progress_updates.get("grayscale", [])[-1] == 1.0
        # Later stages might be incomplete
        assert any(prog < 1.0 for prog in progress_updates.get("enhance", []))
