"""
Processing coordinator module.
"""
import json
import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config.settings import STORAGE_PATHS
from ..enrichment.tmdb_client import TMDBClient
from ..vision.processor import VisionProcessor

class ProcessingCoordinator:
    """Coordinates tape processing workflow."""
    
    def __init__(self):
        """Initialize coordinator."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.vision = VisionProcessor()
        try:
            self.api = TMDBClient()
        except ValueError as e:
            self.logger.warning(f"TMDB client disabled: {e}")
            self.api = None
        
    def _extract_year(self, text: str) -> Optional[str]:
        """
        Extract year from text.
        
        Args:
            text: Input text
            
        Returns:
            Year string if found
        """
        # Look for year in parentheses
        match = re.search(r"\((\d{4})\)", text)
        
        if match:
            return match.group(1)
            
        # Look for standalone year
        match = re.search(r"\b(19|20)\d{2}\b", text)
        
        if match:
            return match.group(0)
            
        return None
        
    def _clean_title(self, text: str) -> str:
        """
        Clean extracted title text.
        
        Args:
            text: Raw title text
            
        Returns:
            Cleaned title
        """
        # Remove year
        text = re.sub(r"\(\d{4}\)", "", text)
        
        # Remove special characters
        text = re.sub(r"[^\w\s-]", "", text)
        
        # Normalize whitespace
        text = " ".join(text.split())
        
        return text.strip()
        
    def _find_best_match(
        self,
        title: str,
        year: Optional[str],
        results: List[Dict]
    ) -> Optional[Dict]:
        """
        Find best matching movie result.
        
        Args:
            title: Movie title
            year: Release year
            results: Search results
            
        Returns:
            Best matching result if found
        """
        if not results:
            return None
            
        # Score results
        scored = []
        
        for result in results:
            score = 0
            
            # Compare titles
            if result["title"].lower() == title.lower():
                score += 3
            elif result["title"].lower() in title.lower():
                score += 2
            elif title.lower() in result["title"].lower():
                score += 1
                
            # Compare years
            if (
                year and
                "release_date" in result and
                result["release_date"].startswith(year)
            ):
                score += 2
                
            # Add to scored list
            scored.append((score, result))
            
        # Sort by score
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Get best match
        if scored and scored[0][0] > 0:
            return scored[0][1]
            
        return None
        
    def _save_results(
        self,
        image_path: str,
        results: Dict
    ) -> str:
        """
        Save processing results.
        
        Args:
            image_path: Path to processed image
            results: Processing results
            
        Returns:
            Path to results file
        """
        # Create filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"vhs_data_{timestamp}.json"
        
        # Create path
        results_path = STORAGE_PATHS["results"] / filename
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add metadata
        results["metadata"] = {
            "image_path": image_path,
            "timestamp": timestamp
        }
        
        # Save JSON
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
            
        return str(results_path)
        
    def process_tape(
        self,
        image_path: str,
        debug: bool = False
    ) -> Dict:
        """
        Process VHS tape image.
        
        Args:
            image_path: Path to tape image
            debug: Enable debug output
            
        Returns:
            Processing results
        """
        try:
            # Process image
            results = self.vision.process_image(image_path)
            
            # Extract titles from OCR results
            titles = []
            
            # Get extracted text
            title_text = results["extracted_data"]["title"]
            if title_text:
                # Split into lines
                lines = title_text.splitlines()
                
                # Process each line
                for line in lines:
                    # Skip short lines
                    if len(line) < 3:
                        continue
                        
                    # Get year
                    year = self._extract_year(line)
                    
                    # Clean title
                    title = self._clean_title(line)
                    
                    # Skip if too short
                    if len(title) < 3:
                        continue
                        
                    # Add to list
                    titles.append(
                        f"{title} ({year})" if year else title
                    )
                    
            results["extracted_titles"] = titles
            
            # Find movie data
            if titles:
                # Search for first title
                title = titles[0]
                year = self._extract_year(title)
                clean_title = self._clean_title(title)
                
                # Find movie data if API client is available
                if self.api:
                    movie_data = self.api.find_best_match(
                        title=clean_title,
                        year=int(year) if year else None
                    )
                    
                    if movie_data:
                        results["movie_data"] = movie_data
                        
            # Save results
            results_path = self._save_results(image_path, results)
            results["results_path"] = results_path
            
            return results
            
        except Exception as e:
            self.logger.exception("Processing error")
            return {
                "success": False,
                "error": str(e)
            }
