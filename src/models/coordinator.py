"""
ProcessingCoordinator handles high-level coordination of image processing and OCR.
"""
import logging
from typing import Dict, Any, Optional
import numpy as np
from PyQt6.QtGui import QImage, QPixmap

from src.vision.processor import VisionProcessor

logger = logging.getLogger(__name__)

class ProcessingCoordinator:
    """Coordinates image processing, OCR extraction, and result management."""
    
    def __init__(self):
        """Initialize coordinator."""
        self.processor = VisionProcessor(save_debug=True)
        self.current_preprocessing_images = {}
        
    def _convert_cv_to_qt(self, image: np.ndarray) -> QPixmap:
        """Convert OpenCV image to Qt pixmap.
        
        Args:
            image: OpenCV image as numpy array (grayscale or color)
            
        Returns:
            QPixmap of the image
        """
        height, width = image.shape[:2]

        # Handle grayscale images
        if len(image.shape) == 2:
            bytes_per_line = width
            # Create QImage with grayscale format
            q_img = QImage(image.data, width, height,
                         bytes_per_line, QImage.Format.Format_Grayscale8)
        else:
            bytes_per_line = 3 * width
            # Convert to RGB for Qt
            image_rgb = image[..., ::-1].copy()
            q_img = QImage(image_rgb.data, width, height,
                          bytes_per_line, QImage.Format.Format_RGB888)

        return QPixmap.fromImage(q_img)
        
    def process_tape(self, image: np.ndarray) -> Dict[str, Any]:
        """Process VHS tape image and extract information.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            # Run vision processing
            raw_result = self.processor.extract_text(image)
            
            # Store preprocessing images for display
            if hasattr(self.processor, 'preprocessing_images'):
                self.current_preprocessing_images = self.processor.preprocessing_images.copy()
            
            # Structure the results in the format expected by ResultsView
            result = {
                "success": raw_result.get("success", False),
                "vision_data": {
                    "title": raw_result.get("text", ""),
                    "confidence": {
                        "title": 0.8,  # Default confidence for now
                    }
                }
            }
            
            if "error" in raw_result:
                result["error"] = raw_result["error"]
                
            return result
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        
    def get_preprocessing_images(self) -> Dict[str, QPixmap]:
        """Get current preprocessing stage images as Qt pixmaps.
        
        Returns:
            Dict mapping stage names to QPixmap images
        """
        pixmaps = {}
        for stage, image in self.current_preprocessing_images.items():
            pixmaps[stage] = self._convert_cv_to_qt(image)
        return pixmaps
        
    def clear(self):
        """Clear current state."""
        self.current_preprocessing_images = {}
        if hasattr(self.processor, 'preprocessing_images'):
            self.processor.preprocessing_images.clear()
