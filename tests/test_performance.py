"""
Performance benchmarking tests for image processing pipeline.
"""
import time
import psutil
import pytest
import cv2
import numpy as np
from pathlib import Path

from src.models.coordinator import ProcessingCoordinator
from src.vision.processor import VisionProcessor
from src.utils import opencv_utils

def get_process_memory():
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

@pytest.fixture
def large_test_image(tmp_path):
    """Create a large test image (4K resolution)."""
    image = np.zeros((2160, 3840, 3), dtype=np.uint8)
    # Add some content
    cv2.rectangle(image, (100, 100), (3740, 2060), (255, 255, 255), -1)
    cv2.putText(image, "LARGE TEST IMAGE", (200, 1080),
                cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 0), 10)
    
    path = tmp_path / "large_test.jpg"
    cv2.imwrite(str(path), image)
    return str(path)

@pytest.fixture
def small_test_image(tmp_path):
    """Create a small test image (720p resolution)."""
    image = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.rectangle(image, (50, 50), (1230, 670), (255, 255, 255), -1)
    cv2.putText(image, "SMALL TEST", (100, 360),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 4)
    
    path = tmp_path / "small_test.jpg"
    cv2.imwrite(str(path), image)
    return str(path)

@pytest.mark.benchmark
def test_preprocessing_performance(large_test_image, small_test_image):
    """Benchmark preprocessing performance on different image sizes."""
    results = []
    
    for image_path in [small_test_image, large_test_image]:
        image = cv2.imread(image_path)
        
        # Time each preprocessing stage
        stages = {
            "grayscale": lambda: opencv_utils.convert_to_grayscale(image),
            "resize": lambda: opencv_utils.resize_image(image, target_width=1024),
            "enhance": lambda: opencv_utils.enhance_contrast(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)),
            "denoise": lambda: opencv_utils.denoise_image(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
        }
        
        stage_times = {}
        for stage_name, stage_func in stages.items():
            start_time = time.time()
            start_memory = get_process_memory()
            
            # Run stage multiple times for average
            for _ in range(5):
                stage_func()
            
            end_time = time.time()
            end_memory = get_process_memory()
            
            stage_times[stage_name] = {
                "time": (end_time - start_time) / 5,  # Average time
                "memory_delta": end_memory - start_memory
            }
        
        results.append({
            "image_size": image.shape,
            "times": stage_times
        })
    
    # Assert performance requirements
    small_results = results[0]
    large_results = results[1]
    
    # Preprocessing should complete within reasonable time
    assert small_results["times"]["grayscale"]["time"] < 0.1
    assert small_results["times"]["resize"]["time"] < 0.2
    assert small_results["times"]["enhance"]["time"] < 0.3
    assert small_results["times"]["denoise"]["time"] < 0.5
    
    # Memory usage should be proportional to image size
    for stage in ["grayscale", "resize", "enhance", "denoise"]:
        small_mem = small_results["times"][stage]["memory_delta"]
        large_mem = large_results["times"][stage]["memory_delta"]
        assert large_mem < small_mem * 10  # Large image shouldn't use 10x more memory

@pytest.mark.benchmark
def test_full_pipeline_performance(large_test_image, small_test_image):
    """Benchmark complete processing pipeline performance."""
    coordinator = ProcessingCoordinator()
    progress_updates = []
    
    def progress_callback(stage: str, progress: float):
        progress_updates.append((stage, progress, time.time()))
    
    for image_path in [small_test_image, large_test_image]:
        start_time = time.time()
        start_memory = get_process_memory()
        
        results = coordinator.process_tape(
            image_path,
            progress_callback=progress_callback
        )
        
        end_time = time.time()
        end_memory = get_process_memory()
        
        processing_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        # Calculate stage durations
        stage_durations = {}
        current_stage = None
        stage_start = None
        
        for stage, progress, timestamp in progress_updates:
            if stage != current_stage:
                if current_stage:
                    stage_durations[current_stage] = timestamp - stage_start
                current_stage = stage
                stage_start = timestamp
        
        # Add final stage duration
        if current_stage:
            stage_durations[current_stage] = end_time - stage_start
        
        # Performance assertions
        assert processing_time < (30 if "large" in image_path else 10), \
            f"Processing took too long: {processing_time:.2f}s"
            
        assert memory_usage < (500 if "large" in image_path else 200), \
            f"Memory usage too high: {memory_usage:.2f}MB"
            
        # Individual stage timing assertions
        if "small" in image_path:
            assert stage_durations.get("grayscale", float("inf")) < 0.5
            assert stage_durations.get("resize", float("inf")) < 1.0
            assert stage_durations.get("enhance", float("inf")) < 1.0
            assert stage_durations.get("denoise", float("inf")) < 2.0
            assert stage_durations.get("text", float("inf")) < 5.0

@pytest.mark.benchmark
def test_concurrent_load_performance():
    """Test performance under concurrent load."""
    coordinator = ProcessingCoordinator()
    processor = VisionProcessor()
    
    # Create multiple test images
    test_images = []
    for i in range(5):
        image = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(image, f"TEST {i}", (100, 360),
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 4)
        test_images.append(image)
    
    start_memory = get_process_memory()
    start_time = time.time()
    
    # Process images sequentially but measure total resource usage
    for image in test_images:
        processor.process_image(image)
    
    end_time = time.time()
    end_memory = get_process_memory()
    
    total_time = end_time - start_time
    total_memory = end_memory - start_memory
    
    # Performance requirements
    assert total_time < len(test_images) * 10, "Sequential processing too slow"
    assert total_memory < 1000, "Memory usage too high under load"

@pytest.mark.benchmark
def test_memory_cleanup():
    """Test memory cleanup after processing."""
    coordinator = ProcessingCoordinator()
    
    # Create test image
    image = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cv2.putText(image, "CLEANUP TEST", (100, 540),
               cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 0), 5)
    
    # Monitor memory through multiple processing cycles
    initial_memory = get_process_memory()
    memory_after_cycles = []
    
    for _ in range(3):
        coordinator.process_tape(image)
        # Force garbage collection
        import gc
        gc.collect()
        memory_after_cycles.append(get_process_memory())
    
    # Memory shouldn't grow significantly across cycles
    memory_growth = max(memory_after_cycles) - initial_memory
    assert memory_growth < 100, "Memory not properly cleaned up between cycles"
