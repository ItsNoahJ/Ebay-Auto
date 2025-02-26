"""
Vision processing module using LM Studio for media image analysis.
"""
import os
from datetime import datetime
from typing import Dict, Any
import cv2

from .lmstudio_vision import VHSVision

class VisionProcessor:
    """
    Handles image processing and text extraction using LM Studio vision model.
    """
    
    def __init__(self, debug_output_dir: str = "debug_output"):
        """Initialize the vision processor."""
        self.debug_output_dir = debug_output_dir
        os.makedirs(debug_output_dir, exist_ok=True)
        
        # Initialize LM Studio vision component
        self.vision = VHSVision(
            model="lmstudio-community/minicpm-o-2_6",
            save_debug=True
        )
        
        # Base confidence threshold
        self.confidence_threshold = 70.0

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process media image with LM Studio vision model.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary containing extracted data and debug info
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
            
        # Extract text for each region
        results = {
            "title": self.vision.extract_info(image, info_type="title"),
            "year": self.vision.extract_info(image, info_type="year"),
            "runtime": self.vision.extract_info(image, info_type="runtime")
        }
        
        # Format results
        extracted_data = {}
        debug_info = {
            "original_image": image_path,
            "confidence_scores": {},
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        }
        
        for field, result in results.items():
            extracted_data[field] = result.get("text", "")
            debug_info["confidence_scores"][field] = result.get("confidence", 0.0)
            
            # Save any error messages
            if "error" in result:
                debug_info.setdefault("errors", {})[field] = result["error"]
                
        return {
            "extracted_data": extracted_data,
            "debug_info": debug_info
        }
        
    def validate_results(self, results: Dict[str, Any]) -> bool:
        """
        Validate results meet confidence threshold.
        
        Args:
            results: Processing results to validate
            
        Returns:
            True if results meet confidence threshold
        """
        if not results or "debug_info" not in results:
            return False
            
        confidence_scores = results["debug_info"].get("confidence_scores", {})
        if not confidence_scores:
            return False
            
        # Check if any field meets threshold
        return any(
            score >= self.confidence_threshold 
            for score in confidence_scores.values()
        )
