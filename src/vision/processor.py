"""
VHS image processing module.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import cv2
import numpy as np

from ..config.settings import TMDB_API_KEY, DISCOGS_CONSUMER_KEY
from ..enrichment.api_client import search_movie_details, search_audio_details
from ..utils import opencv_utils
from .vhs_vision import VHSVision

logger = logging.getLogger(__name__)

class VisionProcessor:
    """Process VHS cover images and extract information."""
    
    def __init__(self, model: str = "local-model", save_debug: bool = False):
        """Initialize processor with model and debug settings."""
        self.vision = VHSVision(model=model, save_debug=save_debug)
        self.save_debug = save_debug
        
        # Check API availability
        self.tmdb_available = bool(TMDB_API_KEY)
        self.discogs_available = bool(DISCOGS_CONSUMER_KEY)
        
        if not self.tmdb_available:
            logger.warning("TMDB API not available - will rely on vision only")
        if not self.discogs_available:
            logger.warning("Discogs API not available - will rely on vision only")
            
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process image and extract media information.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with extracted info and confidence scores
        """
        logger.info(f"Processing image: {image_path}")
        
        # Load image
        image = opencv_utils.load_image(image_path)
        if image is None:
            return self._create_error_result("Failed to load image")
            
        try:
            # Preprocess image
            processed = opencv_utils.preprocess_image(image)
            if self.save_debug:
                self.vision.save_debug_image(processed, "preprocessed")
                
            # Extract all info categories
            results = {}
            categories = ["title", "year", "runtime", "studio", "director", "cast", "rating"]
            for category in categories:
                results[category] = self.vision.extract_info(processed, category)
                
            # Build base result from vision
            vision_result = {
                "title": results["title"]["text"],
                "year": results["year"]["text"],
                "runtime": results["runtime"]["text"],
                "studio": results["studio"]["text"],
                "director": results["director"]["text"],
                "cast": results["cast"]["text"],
                "rating": results["rating"]["text"],
                "confidence": {
                    category: results[category]["confidence"]
                    for category in categories
                },
                "source": {
                    category: "vision"
                    for category in categories
                }
            }
            
            # Check if we need API backup for any low confidence results
            if self.tmdb_available and self._needs_api_backup(vision_result):
                api_result = search_movie_details(vision_result["title"])
                
                # Update low confidence fields with API data
                vision_result.update(
                    self._merge_api_results(vision_result, api_result)
                )
                
            return vision_result
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return self._create_error_result(str(e))
            
    def _needs_api_backup(self, result: Dict[str, Any], threshold: float = 70.0) -> bool:
        """Check if any field needs API backup based on confidence."""
        return any(
            conf < threshold 
            for conf in result["confidence"].values()
        )
        
    def _merge_api_results(self, vision_result: Dict[str, Any], api_result: Dict[str, Any]) -> Dict[str, Any]:
        """Merge API results for low confidence fields."""
        merged = vision_result.copy()
        
        # Only update fields where vision confidence is low
        confidence_threshold = 70.0
        
        # Base fields that can come from TMDB
        base_fields = ["title", "year", "runtime"]
        # Additional fields that might be available from TMDB
        extra_fields = ["studio", "director", "cast"]
        
        for field in base_fields + extra_fields:
            if (vision_result["confidence"][field] < confidence_threshold 
                and api_result.get(field)):
                merged[field] = api_result[field]
                merged["confidence"][field] = 85.0  # Standard API confidence
                merged["source"][field] = "api"
                
        return merged
            
    def _create_error_result(self, error: str) -> Dict[str, Any]:
        """Create error result dictionary."""
        categories = ["title", "year", "runtime", "studio", "director", "cast", "rating"]
        return {
            category: "" for category in categories
        } | {
            "confidence": {category: 0 for category in categories},
            "source": {category: "none" for category in categories},
            "error": error
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
            
        required_fields = [
            "title", "year", "runtime", "studio", 
            "director", "cast", "rating",
            "confidence", "source"
        ]
        
        for field in required_fields:
            if field not in results:
                logger.error(f"Missing required field: {field}")
                return False
                
        # At least one field should have non-zero confidence
        confidence = results["confidence"]
        if not any(conf > 0 for conf in confidence.values()):
            logger.error("No fields extracted with confidence")
            return False
            
        return True
