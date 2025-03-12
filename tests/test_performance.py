"""Performance testing for vision processing."""
import pytest
import cv2
import numpy as np
import time
import psutil
import os
import requests
from typing import Dict, Tuple
from unittest.mock import Mock

from src.vision.lmstudio_vision import VHSVision
from src.utils.opencv_utils import load_image

# Ensure test data directory exists
TEST_DATA_DIR = os.path.join("tests", "test_data")
if not os.path.exists(TEST_DATA_DIR):
    os.makedirs(TEST_DATA_DIR)

def get_memory_usage() -> Tuple[float, float]:
    """Get current memory usage."""
    process = psutil.Process(os.getpid())
    mem = process.memory_info()
    return mem.rss / 1024 / 1024, mem.vms / 1024 / 1024  # RSS and VMS in MB

def load_test_images() -> Dict[str, np.ndarray]:
    """Load test images of different sizes."""
    test_images = {}
    base_path = "tests/test_data"
    
    # Load sample images
    image_files = [
        "sample_vhs.jpg",
        "testvhs.jpg",
        "testvhs2.jpg",
        "testvhs3.jpg"
    ]
    
    for filename in image_files:
        path = os.path.join(base_path, filename)
        if os.path.exists(path):
            test_images[filename] = load_image(path)
    
    return test_images

@pytest.fixture
def vision(monkeypatch):
    """Initialize vision processor for testing."""
    # Mock LM Studio API responses for consistent testing
    def mock_post(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            
            def json(self):
                return {
                    "choices": [{
                        "message": {"content": "Test Movie Title"}
                    }]
                }
            
            def raise_for_status(self):
                pass
                
        return MockResponse()
        
    def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            
            def json(self):
                return [{
                    "id": "test-model",
                    "name": "Test Model"
                }]
                
        return MockResponse()
        
    # Apply mocks
    monkeypatch.setattr(requests, "post", mock_post)
    monkeypatch.setattr(requests, "get", mock_get)
    
    # Initialize with mocked API
    return VHSVision(save_debug=False)  # Disable debug for performance testing

def test_preprocessing_performance(vision, benchmark):
    """Test preprocessing performance."""
    test_images = load_test_images()
    if not test_images:
        pytest.skip("No test images available")
        
    image = list(test_images.values())[0]
    
    def run_preprocessing():
        return vision.preprocess_image(image)
        
    # Run benchmark
    benchmark(run_preprocessing)
    
    # Verify output quality
    result = vision.preprocess_image(image)
    assert result is not None
    assert result.shape[2] == 3  # Should be BGR
    assert result.dtype == np.uint8

def test_extract_info_performance(vision):
    """Test end-to-end performance of info extraction."""
    test_images = load_test_images()
    if not test_images:
        pytest.skip("No test images available")
        
    results = []
    mem_usage = []
    
    for name, image in test_images.items():
        # Measure initial memory
        initial_rss, initial_vms = get_memory_usage()
        
        # Time the extraction
        start_time = time.time()
        result = vision.extract_info(image)
        elapsed = time.time() - start_time
        
        # Measure final memory
        final_rss, final_vms = get_memory_usage()
        
        # Record metrics
        metrics = {
            "image": name,
            "resolution": f"{image.shape[1]}x{image.shape[0]}",
            "time": elapsed,
            "memory_increase": {
                "rss": final_rss - initial_rss,
                "vms": final_vms - initial_vms
            },
            "success": result.get("success", False),
            "confidence": result.get("confidence", 0.0)
        }
        results.append(metrics)
        
        # Performance assertions with relaxed timing for CI environments
        assert elapsed < 20.0, f"Processing took too long: {elapsed:.2f}s"
        assert (final_rss - initial_rss) < 1000, "Memory usage increased too much"  # Allow more memory for testing
        
    # Log results
    print("\nPerformance Test Results:")
    print("=" * 50)
    for r in results:
        print(f"\nImage: {r['image']}")
        print(f"Resolution: {r['resolution']}")
        print(f"Processing Time: {r['time']:.2f}s")
        print(f"Memory Increase: RSS={r['memory_increase']['rss']:.1f}MB, VMS={r['memory_increase']['vms']:.1f}MB")
        print(f"Success: {r['success']}")
        print(f"Confidence: {r['confidence']:.2f}")
    print("=" * 50)

def test_image_encoding_performance(vision, benchmark):
    """Test performance of image encoding."""
    test_images = load_test_images()
    if not test_images:
        pytest.skip("No test images available")
        
    image = list(test_images.values())[0]
    processed = vision.preprocess_image(image)
    
    def run_encoding():
        return vision.encode_image(processed)
        
    # Run benchmark
    result = benchmark(run_encoding)
    
    # Verify encoded size
    encoded = vision.encode_image(processed)
    assert len(encoded) <= vision.target_encoded_size * 1.1  # Allow 10% margin

def test_api_call_performance(vision):
    """Test LM Studio API call performance."""
    test_images = load_test_images()
    if not test_images:
        pytest.skip("No test images available")
        
    image = list(test_images.values())[0]
    
    # Time multiple API calls
    times = []
    for _ in range(3):  # Test 3 calls
        start_time = time.time()
        result = vision.extract_info(image)
        elapsed = time.time() - start_time
        times.append(elapsed)
        
        # Verify basic result structure
        assert isinstance(result, dict)
        assert "text" in result
        assert "confidence" in result
        
        # Performance assertions with relaxed timing
        assert elapsed < 20.0, f"API call took too long: {elapsed:.2f}s"
        
    # Calculate statistics
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    
    print("\nAPI Call Performance:")
    print(f"Average Time: {avg_time:.2f}s")
    print(f"Min Time: {min_time:.2f}s")
    print(f"Max Time: {max_time:.2f}s")
