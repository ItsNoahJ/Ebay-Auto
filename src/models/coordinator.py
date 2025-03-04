"""
Media processing coordinator.
"""
from datetime import datetime
import json
import logging
import os
from pathlib import Path
from typing import Optional, Callable, Dict, Any

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
        self.vision_processor = VisionProcessor(save_debug=True)
        
    def process_tape(
        self,
        image_path: str,
        media_type: str = "MOVIE",
        debug: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Process a media cover image.
        
        Args:
            image_path: Path to image file
            media_type: Type of media (MOVIE, CD, VINYL, CASSETTE)
            debug: Enable debug visualization
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict containing processing results
        """
        logger.info(f"Processing {image_path}")
        
        def update_progress(stage: str, progress: float):
            """Helper to update progress if callback exists."""
            if progress_callback:
                progress_callback(stage, progress)
        
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
            # Check if image exists
            if not os.path.exists(image_path):
                results["error"] = f"Image not found: {image_path}"
                return results
                
            # Process image with vision model (this will handle preprocessing progress)
            vision_results = self.vision_processor.process_image(
                image_path,
                progress_callback=progress_callback
            )
            
            # Update results with vision data and status
            results["vision_data"] = vision_results.get("vision_data", {})
            results["success"] = vision_results.get("success", False)
            
            # Copy error message if present
            if "error" in vision_results:
                results["error"] = vision_results["error"]
                return results
            
            # Start text extraction progress
            update_progress("text", 0.0)
                
            # Extract title from vision results if available
            if "vision_data" in vision_results:
                title = vision_results["vision_data"].get("title")
                if title:
                    results["extracted_titles"] = vision_results.get("extracted_titles", [title])
                    
                    # Update progress before API enrichment
                    update_progress("text", 0.8)
                    
                    # Enrich with metadata based on media type
                    if media_type == "MOVIE":
                        update_progress("text", 0.9)
                        results["movie_data"] = search_movie_details(title)
                    elif media_type in ["CD", "VINYL", "CASSETTE"]:
                        update_progress("text", 0.9)
                        results["audio_data"] = search_audio_details(title, media_type)
                    
                    update_progress("text", 1.0)
            
            # Save results if successful
            if results["success"]:
                results_path = self._save_results(results)
                results["results_path"] = str(results_path)
            
        except (IOError, cv2.error) as e:
            logger.error(f"Error reading image {image_path}: {str(e)}")
            results["success"] = False
            results["error"] = f"Failed to read image: {str(e)}"
        except Exception as e:
            logger.error(f"Error processing {image_path}: {str(e)}")
            results["success"] = False
            results["error"] = f"Processing error: {str(e)}"
            
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
        
    def validate_results(self, results: Dict[str, Any]) -> bool:
        """
        Validate processing results.
        
        Args:
            results: Results dictionary from process_tape()
            
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
