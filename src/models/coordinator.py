"""
Media processing coordinator.
"""
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import cv2

from ..vision.processor import VisionProcessor
from ..enrichment.api_client import (
    search_movie_details, 
    search_audio_details,
    create_empty_movie_result,
    create_empty_audio_result
)
from ..config.settings import STORAGE_PATHS

logger = logging.getLogger(__name__)

class ProcessingCoordinator:
    """Coordinates the media processing pipeline."""
    
    def __init__(self):
        """Initialize coordinator."""
        # Initialize vision processor with debug output enabled
        self.vision_processor = VisionProcessor(debug_output_dir="debug_output")
        
    def process_tape(self, image_path: str, media_type: str = "MOVIE", debug: bool = False) -> dict:
        """
        Process a media cover image.
        
        Args:
            image_path: Path to image file
            media_type: Type of media (MOVIE, CD, VINYL, CASSETTE)
            debug: Enable debug visualization (unused, debug is set in processor init)
            
        Returns:
            Dict containing processing results
        """
        logger.info(f"Processing {image_path}")
        
        # Initialize results
        results = {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "media_type": media_type,
            "extracted_titles": [],
            "movie_data": create_empty_movie_result() if media_type == "MOVIE" else None,
            "audio_data": create_empty_audio_result() if media_type in ["CD", "VINYL", "CASSETTE"] else None,
            "vision_data": None,
            "debug_image": None,
            "results_path": None
        }
        
        try:
            # Process image with vision model
            vision_results = self.vision_processor.process_image(image_path)
            
            # Check vision processing success
            if not self.vision_processor.validate_results(vision_results):
                results["error"] = "Vision processing failed validation"
                return results
                
            # Update results with vision data
            results["vision_data"] = vision_results
            results["success"] = True
            
            # Extract title from vision results if available
            if "extracted_data" in vision_results:
                title = vision_results["extracted_data"].get("title")
                if title:
                    results["extracted_titles"].append(title)
                    
                    # Enrich with metadata based on media type
                    if media_type == "MOVIE":
                        results["movie_data"] = search_movie_details(title)
                    elif media_type in ["CD", "VINYL", "CASSETTE"]:
                        results["audio_data"] = search_audio_details(title, media_type)
            
            # Save results
            if results["success"]:
                results_path = self._save_results(results)
                results["results_path"] = str(results_path)
            
        except Exception as e:
            logger.error(f"Error processing {image_path}: {str(e)}")
            results["success"] = False
            results["error"] = str(e)
            
        return results
        
    def _save_results(self, results: dict) -> Path:
        """
        Save processing results to JSON file.
        
        Args:
            results: Results dictionary
            
        Returns:
            Path to saved results file
        """
        # Create results directory
        results_dir = STORAGE_PATHS["results"]
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = results_dir / f"results_{timestamp}.json"
        
        # Save to file
        with open(results_path, "w") as f:
            # Convert results to serializable format
            clean_results = results.copy()
            clean_results["timestamp"] = results["timestamp"]
            clean_results.pop("debug_image", None)  # Remove debug image
            
            json.dump(clean_results, f, indent=2)
            
        return results_path
