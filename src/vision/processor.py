"""
Core vision processing functionality.
"""
import os
import logging
import cv2
import numpy as np
from typing import Optional, Dict, Any

from src.vision.vhs_vision import VHSVision
from src.vision.preprocessing import TimeoutError

logger = logging.getLogger(__name__)

class VisionProcessor:
    """Handles image preprocessing and OCR extraction."""
    
    def __init__(self, save_debug: bool = False):
        """Initialize vision processor."""
        self.save_debug = save_debug
        if save_debug:
            os.makedirs("debug_output", exist_ok=True)
            logger.info("Created debug output directory: debug_output")
            
        # Initialize vision backend
        try:
            self.vision = VHSVision()
            # Basic test image for OCR
            test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255  # White background
            cv2.putText(test_img, "TEST", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
            
            # Test basic OCR functionality
            result = self.vision.extract_text(test_img)
            if not result or result.get("success") is False:
                logger.error(f"LM Studio test failed: {result.get('error', 'Unknown error')}")
                raise Exception("LM Studio connection test failed")
            logger.info("LM Studio vision backend initialized successfully")
        except Exception as e:
            logger.warning(f"Vision backend not available - will rely on vision only: {str(e)}")
            self.vision = None
            
        # Store preprocessing stage images
        self.preprocessing_images: Dict[str, np.ndarray] = {}

    def store_preprocessing_image(self, stage: str, image: np.ndarray) -> None:
        """Store preprocessing stage image with validation.
        
        Args:
            stage: Name of the preprocessing stage
            image: Image array (2D grayscale or 3D color)
        """
        if image is None:
            raise ValueError("Image cannot be None")
            
        if not isinstance(image, np.ndarray):
            raise TypeError(f"Expected numpy array, got {type(image)}")
            
        # Handle both 2D grayscale and 3D color images
        if len(image.shape) not in [2, 3]:
            raise ValueError(f"Expected 2D or 3D image array, got shape {image.shape}")
            
        self.preprocessing_images[stage] = image

    def get_preprocessing_image(self, stage: str) -> Optional[np.ndarray]:
        """Get preprocessing stage image if it exists."""
        return self.preprocessing_images.get(stage)

    def clear_preprocessing_images(self) -> None:
        """Clear all preprocessing stage images."""
        self.preprocessing_images.clear()

    def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text from image using vision backend.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dict containing extracted text and metadata
            
        Raises:
            TimeoutError: If processing exceeds timeout
        """
        if self.vision is None:
            return {"success": False, "error": "Vision backend not available"}
            
        # Store original
        self.store_preprocessing_image("Original", image)
        
        # Run extraction
        try:
            result = self.vision.extract_text(image)
            
            # Store any debug images from vision backend
            if hasattr(self.vision, 'preprocessing_images'):
                for stage, img in self.vision.preprocessing_images.items():
                    self.store_preprocessing_image(stage, img)
                    
            return result
            
        except TimeoutError as e:
            # Re-raise timeout errors
            logger.error(f"Error extracting text: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return {
                "success": False,
                "error": f"Text extraction failed: {str(e)}"
            }
