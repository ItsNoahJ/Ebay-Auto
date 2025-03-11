"""
Mock objects and utilities for testing.
"""
import time
import numpy as np
import cv2

from src.vision.preprocessing import TimeoutError

def create_test_image(width: int = 640, height: int = 480) -> np.ndarray:
    """
    Create a test image with some text-like regions for testing.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        
    Returns:
        NumPy array representing the test image
    """
    # Create blank image
    image = np.full((height, width), 255, dtype=np.uint8)
    
    # Add some text-like regions
    cv2.putText(
        image,
        "MOVIE TITLE",
        (50, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        0,
        4
    )
    
    cv2.putText(
        image,
        "1985",
        (50, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        0,
        2
    )
    
    cv2.putText(
        image,
        "STUDIO",
        (50, 300),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        0,
        2
    )
    
    # Add some noise and blur to simulate real conditions
    noise = np.random.normal(0, 10, image.shape).astype(np.uint8)
    image = cv2.add(image, noise)
    image = cv2.GaussianBlur(image, (3, 3), 0)
    
    return image

class MockVHSVision:
    """Mock VHS vision processor for testing."""
    
    def __init__(self, *args, **kwargs):
        """Initialize mock."""
        self.save_debug = kwargs.get('save_debug', False)
        self.pipeline = MockPreprocessor()
        self._preprocessing_images = {
            "Grayscale": np.zeros((100, 100, 3), dtype=np.uint8),
            "Enhanced": np.zeros((100, 100, 3), dtype=np.uint8)
        }
        
    @property
    def preprocessing_images(self):
        """Get preprocessing stage images."""
        return self._preprocessing_images
    
    @preprocessing_images.setter
    def preprocessing_images(self, value):
        """Set preprocessing stage images."""
        self._preprocessing_images = value

    def check_models(self) -> bool:
        """Check if models are available."""
        return True
        
    def extract_text(self, image: np.ndarray):
        """Return mock extracted info matching VisionProcessor expectations."""
        return {
            "success": True,
            "vision_data": {
                "title": "Mock Title",
                "year": "1985",
                "runtime": "120 min",
                "confidence": {
                    "title": 0.95,
                    "year": 0.90,
                    "runtime": 0.85
                }
            }
        }

class MockVHSVisionWithTimeout(MockVHSVision):
    """Mock VHS vision processor that simulates timeouts."""
    
    def __init__(self, *args, **kwargs):
        """Initialize mock with delay settings."""
        super().__init__(*args, **kwargs)
        self.processing_delay = kwargs.get('processing_delay', 2)  # Seconds per stage
        self.pipeline = PreprocessorWithTimeout(processing_delay=self.processing_delay)
        self.timeout = None
        
    def extract_text(self, image: np.ndarray):
        """Simulate processing with potential timeout."""
        # Simulate processing time
        time.sleep(self.processing_delay)
        
        # Check if we would have timed out
        if self.timeout and self.processing_delay > self.timeout:
            raise TimeoutError(f"Processing timed out after {self.timeout} seconds")
            
        return {
            "success": True,
            "vision_data": {
                "title": "Mock Title",
                "year": "1985",
                "runtime": "120 min",
                "confidence": {
                    "title": 0.85,
                    "year": 0.80,
                    "runtime": 0.75
                }
            }
        }

class MockPreprocessor:
    """Mock preprocessor for testing."""
    
    def __init__(self, *args, **kwargs):
        """Initialize mock."""
        pass
        
    def preprocess(self, image, progress_callback=None, timeout=None):
        """Return mock preprocessed image with test regions."""
        # Create mock regions for testing
        from src.vision.preprocessing import TextRegion
        mock_regions = [
            TextRegion(10, 10, 100, 50, image[10:60, 10:110]),  # Mock title region
            TextRegion(10, 70, 80, 30, image[70:100, 10:90])    # Mock year region
        ]
        return image, mock_regions

class PreprocessorWithTimeout(MockPreprocessor):
    """Mock preprocessor that simulates timeouts."""
    
    def __init__(self, *args, **kwargs):
        """Initialize mock with delay settings."""
        super().__init__(*args, **kwargs)
        self.processing_delay = kwargs.get('processing_delay', 1)  # Seconds per stage
        
    def preprocess(self, image, progress_callback=None, timeout=None):
        """Simulate preprocessing with delay."""
        start_time = time.time()
        
        # Update progress for early stages
        if progress_callback:
            stages = ["grayscale", "resize", "enhance", "denoise"]
            for stage in stages:
                progress_callback(stage, 0.0)
                time.sleep(0.1)  # Small delay
                if timeout and (time.time() - start_time) > timeout:
                    # Show partial progress for current stage
                    progress_callback(stage, 0.5)
                    raise TimeoutError(f"Preprocessing timed out after {timeout} seconds")
                progress_callback(stage, 1.0)
            
            # Text progress is handled separately
            progress_callback("text", 0.0)
            
        # Simulate main processing time
        if self.processing_delay:
            time.sleep(self.processing_delay)
            
        # Check for timeout after delay
        if timeout and (time.time() - start_time) > timeout:
            if progress_callback:
                progress_callback("text", 0.5)  # Show text as partially complete
            raise TimeoutError(f"Preprocessing timed out after {timeout} seconds")
            
        # If we get here, text is complete
        if progress_callback:
            progress_callback("text", 1.0)
            
        # Create mock regions for testing
        from src.vision.preprocessing import TextRegion
        mock_regions = [
            TextRegion(10, 10, 100, 50, image[10:60, 10:110]),  # Mock title region
            TextRegion(10, 70, 80, 30, image[70:100, 10:90])    # Mock year region
        ]
        
        # Return mock result with regions
        return image, mock_regions
        
    def save_debug_image(self, image, name):
        """Mock saving debug image."""
        pass

class MockAPIClient:
    """Mock API client for testing."""
    
    def __init__(self, *args, **kwargs):
        """Initialize mock."""
        self.processing_delay = kwargs.get('processing_delay', 0)
        self.should_timeout = kwargs.get('should_timeout', False)
        self.error_rate = kwargs.get('error_rate', 0.0)
        
    def search_movie(self, title, timeout=None):
        """Return mock movie data with simulated delays/errors."""
        # Simulate processing delay
        if self.processing_delay:
            time.sleep(self.processing_delay)
            
        # Check for timeout
        if timeout and self.processing_delay > timeout:
            raise TimeoutError(f"API request timed out after {timeout} seconds")
            
        # Simulate random errors
        if self.error_rate > 0 and np.random.random() < self.error_rate:
            raise Exception("Simulated API error")
            
        # Return mock data
        return {
            "title": title,
            "year": "1985",
            "runtime": "116",
            "studio": "Mock Studio",
            "director": "John Director",
            "cast": "Actor One, Actor Two",
            "rating": "PG"
        }
        
    def search_audio(self, title, media_type, timeout=None):
        """Return mock audio data with simulated delays/errors."""
        # Simulate processing delay
        if self.processing_delay:
            time.sleep(self.processing_delay)
            
        # Check for timeout
        if timeout and self.processing_delay > timeout:
            raise TimeoutError(f"API request timed out after {timeout} seconds")
            
        # Simulate random errors
        if self.error_rate > 0 and np.random.random() < self.error_rate:
            raise Exception("Simulated API error")
            
        # Return mock data
        return {
            "title": title,
            "artist": "Mock Artist",
            "year": "1985",
            "genre": "Rock",
            "label": "Mock Records"
        }

class MockStatusWidget:
    """Mock status widget for testing."""
    
    def __init__(self):
        """Initialize mock."""
        self.status = "connected"
        self.animation_running = False
        
    def start_loading_animation(self):
        """Start mock loading animation."""
        self.animation_running = True
        
    def stop_loading_animation(self):
        """Stop mock loading animation."""
        self.animation_running = False
        
    def check_connection(self):
        """Return mock connection status."""
        return True
        
    def update_status(self, status):
        """Update mock status."""
        self.status = status
