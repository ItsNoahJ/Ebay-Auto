"""
Mock classes for testing.
"""
from unittest.mock import MagicMock

class MockVisionResponse:
    """Mock vision API response."""
    
    def __init__(self, text: str = "", confidence: float = 0.0):
        self.text = text
        self.confidence = confidence
        
    def json(self):
        """Return response in the format expected by VHSVision."""
        return {
            "choices": [
                {
                    "message": {
                        "content": self.text
                    }
                }
            ]
        }

class MockLMStudioAPI(MagicMock):
    """Mock LM Studio API client."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_code = 200
        
    def json(self):
        return {
            "models": [
                {
                    "id": "test-model",
                    "name": "Test Model"
                }
            ]
        }

class MockVisionProcessor:
    """Mock vision processor for testing."""
    
    def __init__(self, save_debug: bool = False):
        self.save_debug = save_debug
        self.processed_images = []
        
    def process_image(self, image_path: str):
        """Mock image processing with test responses."""
        self.processed_images.append(image_path)
        
        # Return test results matching the expected structure
        vision_data = {
            "title": "Test Movie",
            "year": "1985",
            "runtime": "1h 30m",
            "studio": "Test Studio",
            "director": "Test Director",
            "cast": "Test Cast",
            "rating": "PG",
            "confidence": {
                "title": 0.8,  # High confidence for normal title
                "year": 0.9,
                "runtime": 0.8,
                "studio": 0.7,
                "director": 0.7,
                "cast": 0.7,
                "rating": 0.7
            },
            "source": {
                "title": "vision",
                "year": "vision",
                "runtime": "vision",
                "studio": "vision",
                "director": "vision",
                "cast": "vision",
                "rating": "vision"
            }
        }
        
        return {
            "success": True,
            "vision_data": vision_data,
            "extracted_titles": ["Test Movie"],
            "image_path": image_path,
            "debug_image": None,
            "audio_data": None
        }
        
    def validate_results(self, results):
        """Mock results validation."""
        return True

class MockLongTitleProcessor(MockVisionProcessor):
    """Mock processor that returns a long title with low confidence."""
    
    def process_image(self, image_path: str):
        """Return results with a long title and low confidence."""
        vision_data = {
            "title": "A Very Very Long Movie Title That Should Have Low Confidence",
            "year": "1985",
            "runtime": "1h 30m",
            "studio": "Test Studio",
            "director": "Test Director",
            "cast": "Test Cast",
            "rating": "PG",
            "confidence": {
                "title": 0.3,  # Low confidence for long title
                "year": 0.9,
                "runtime": 0.8,
                "studio": 0.7,
                "director": 0.7,
                "cast": 0.7,
                "rating": 0.7
            },
            "source": {
                key: "vision" for key in ["title", "year", "runtime", "studio", "director", "cast", "rating"]
            }
        }
        
        return {
            "success": True,
            "vision_data": vision_data,
            "extracted_titles": ["A Very Very Long Movie Title That Should Have Low Confidence"],
            "image_path": image_path,
            "debug_image": None,
            "audio_data": None
        }

class MockErrorProcessor(MockVisionProcessor):
    """Mock processor that simulates errors."""
    
    def process_image(self, image_path: str):
        """Return error results."""
        fields = ["title", "year", "runtime", "studio", "director", "cast", "rating"]
        vision_data = {
            field: "" for field in fields
        }
        vision_data.update({
            "confidence": {field: 0.0 for field in fields},
            "source": {field: "none" for field in fields}
        })
        
        return {
            "success": False,
            "vision_data": vision_data,
            "extracted_titles": [],
            "image_path": image_path,
            "debug_image": None,
            "audio_data": None,
            "error": "Mock processing error"
        }
