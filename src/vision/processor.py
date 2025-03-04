"""
VHS image processing module.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable

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
        # Create debug output directory if needed
        if save_debug:
            debug_dir = Path("debug_output")
            debug_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created debug output directory: {debug_dir}")
            
        self.vision = VHSVision(model=model, save_debug=save_debug)
        self.save_debug = save_debug
        
        # Check API availability
        self.tmdb_available = bool(TMDB_API_KEY)
        self.discogs_available = bool(DISCOGS_CONSUMER_KEY)
        
        if not self.tmdb_available:
            logger.warning("TMDB API not available - will rely on vision only")
        if not self.discogs_available:
            logger.warning("Discogs API not available - will rely on vision only")
            
    def process_image(self, image_path: str, progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Any]:
        """
        Process image and extract media information.
        
        Args:
            image_path: Path to image file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with extracted info and confidence scores
        """
        logger.info(f"Processing image: {image_path}")
        
        def update_progress(stage: str, progress: float):
            """Helper to update progress if callback exists."""
            if progress_callback:
                progress_callback(stage, progress)
        
        # Load image
        update_progress("grayscale", 0.0)
        image = opencv_utils.load_image(image_path)
        if image is None:
            return self._create_error_result("Failed to load image")
        update_progress("grayscale", 0.5)
            
        try:
            # Convert to grayscale first
            grayscale = opencv_utils.convert_to_grayscale(image)
            update_progress("grayscale", 1.0)
            
            # Resize image
            update_progress("resize", 0.0)
            resized = opencv_utils.resize_image(grayscale)
            update_progress("resize", 1.0)
            
            # Enhance contrast
            update_progress("enhance", 0.0)
            enhanced = opencv_utils.enhance_contrast(resized)
            update_progress("enhance", 1.0)
            
            # Denoise
            update_progress("denoise", 0.0)
            denoised = opencv_utils.denoise_image(enhanced)
            update_progress("denoise", 1.0)
            
            # Text detection and extraction
            update_progress("text", 0.0)
            if self.save_debug:
                self.vision.save_debug_image(denoised, "preprocessed")
                
            # Extract info categories with progress updates
            categories = ["title", "year", "runtime", "studio", "director", "cast", "rating"]
            total_categories = len(categories)
            
            # Extract info with confidence scores
            extracted_data = {}
            confidence_scores = {}
            
            for idx, category in enumerate(categories):
                try:
                    result = self.vision.extract_info(denoised, category)
                    text = result.get("text", "")
                    # Ensure confidence is in decimal form (0.0-1.0)
                    confidence = float(result.get("confidence", 0.0))
                    if confidence > 1.0:  # Convert percentage to decimal if needed
                        confidence = confidence / 100.0
                        
                    extracted_data[category] = text
                    confidence_scores[category] = confidence
                except Exception as e:
                    logger.error(f"Error extracting {category}: {e}")
                    extracted_data[category] = ""
                    confidence_scores[category] = 0.0
                    
                update_progress("text", (idx + 1) / total_categories)
            
            # Build base result
            vision_result = {
                **extracted_data,
                "confidence": confidence_scores,
                "extracted_data": extracted_data,
                "source": {
                    category: "vision"
                    for category in categories
                },
                "success": True  # Indicate successful processing
            }
            
            # Check if we need API backup for any low confidence results
            try:
                if self.tmdb_available and self._needs_api_backup(vision_result):
                    api_result = search_movie_details(vision_result["title"])
                    if api_result:
                        # Update low confidence fields with API data
                        vision_result = self._merge_api_results(vision_result, api_result)
            except Exception as e:
                logger.error(f"API backup error: {e}")
                # Continue with vision results on API error
                
            return vision_result
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return self._create_error_result(str(e))
            
    def _needs_api_backup(self, result: Dict[str, Any], threshold: float = 0.7) -> bool:
        """Check if any field needs API backup based on confidence."""
        return any(
            conf < threshold 
            for conf in result["confidence"].values()
        )
        
    def _merge_api_results(self, vision_result: Dict[str, Any], api_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge API results for low confidence fields.
        
        Args:
            vision_result: Original results from vision processing
            api_result: Results from API lookup
            
        Returns:
            Updated results dictionary with API data merged in
        """
        merged = vision_result.copy()
        confidence_threshold = 0.7
        
        # Ensure api_result fields match our expected format
        api_data = {
            "title": str(api_result.get("title", "")),
            "year": str(api_result.get("year", "")),
            "runtime": str(api_result.get("runtime", "")),
            "studio": str(api_result.get("studio", "")),
            "director": str(api_result.get("director", "")),
            "cast": str(api_result.get("cast", ""))
        }
        
        # First verify any fields exist in API result
        if not any(api_data.values()):
            logger.warning("No valid data found in API result")
            return merged
            
        # Update fields from API if they meet criteria
        for field, api_value in api_data.items():
            if api_value and (
                field not in vision_result or
                not vision_result[field] or
                vision_result["confidence"].get(field, 0) < confidence_threshold
            ):
                logger.debug(f"Updating {field} from API: {api_value}")
                merged[field] = api_value
                merged["confidence"][field] = 0.85
                merged["source"][field] = "api"  # Explicitly mark source as API
                
        return merged
            
    def _create_error_result(self, error: str) -> Dict[str, Any]:
        """Create error result dictionary."""
        categories = ["title", "year", "runtime", "studio", "director", "cast", "rating"]
        return {
            category: "" for category in categories
        } | {
            "confidence": {category: 0 for category in categories},
            "source": {category: "none" for category in categories},
            "error": error,
            "success": False
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
