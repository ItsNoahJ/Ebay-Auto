"""
Vision processing module.
"""
import logging
from pathlib import Path
from typing import Dict, Any

import cv2

from ..utils.opencv_utils import (
    load_image,
    preprocess_image,
    normalize_image,
    extract_text_regions
)
from .vhs_vision import VHSVision

logger = logging.getLogger(__name__)

class VisionProcessor:
    """Vision processing pipeline."""
    
    def __init__(self, debug_output_dir: str = None):
        """
        Initialize processor.
        
        Args:
            debug_output_dir: Directory for debug output images. If None, debug is disabled.
        """
        self.debug = debug_output_dir is not None
        self.debug_dir = debug_output_dir
        
        # Initialize vision model
        self.vision = VHSVision(save_debug=self.debug)
        
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process VHS cover image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary containing processing results
        """
        logger.info(f"Processing image: {image_path}")
        
        try:
            # Load and preprocess image
            image = load_image(image_path)
            if image is None:
                return {
                    "success": False,
                    "error": f"Failed to load image: {image_path}"
                }
                
            # Save original for debug
            if self.debug:
                self.vision.save_debug_image(
                    image, 
                    "original",
                    self.debug_dir
                )
                
            # Preprocess image
            preprocessed = preprocess_image(image)
            if self.debug:
                self.vision.save_debug_image(
                    preprocessed,
                    "preprocessed",
                    self.debug_dir
                )
            
            # Extract info
            results = {
                "success": True,
                "image_path": image_path,
                "extracted_data": {}
            }
            
            # Extract title
            title_result = self.vision.extract_info(preprocessed, "title")
            if title_result["text"]:
                results["extracted_data"]["title"] = title_result["text"]
                results["extracted_data"]["title_confidence"] = title_result["confidence"]
                
            # Extract year
            year_result = self.vision.extract_info(preprocessed, "year") 
            if year_result["text"]:
                results["extracted_data"]["year"] = year_result["text"]
                results["extracted_data"]["year_confidence"] = year_result["confidence"]
                
            # Extract runtime
            runtime_result = self.vision.extract_info(preprocessed, "runtime")
            if runtime_result["text"]:
                results["extracted_data"]["runtime"] = runtime_result["text"]
                results["extracted_data"]["runtime_confidence"] = runtime_result["confidence"]
            
            return results
            
        except Exception as e:
            logger.exception(f"Processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def validate_results(self, results: Dict[str, Any]) -> bool:
        """
        Validate processing results.
        
        Args:
            results: Results dictionary from process_image()
            
        Returns:
            True if results are valid, False otherwise
        """
        if not isinstance(results, dict):
            logger.error("Results is not a dictionary")
            return False
            
        if not results.get("success", False):
            logger.error("Processing was not successful")
            return False
            
        if "extracted_data" not in results:
            logger.error("No extracted data in results")
            return False
            
        extracted = results["extracted_data"]
        if not extracted:
            logger.error("Extracted data is empty")
            return False
            
        # Should have at least title
        if "title" not in extracted:
            logger.error("No title in extracted data")
            return False
            
        return True
