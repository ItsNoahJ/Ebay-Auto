"""
Command-line interface module.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

from .config.settings import validate_settings
from .models.coordinator import ProcessingCoordinator

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def process_image(image_path: str, debug: bool = False) -> bool:
    """
    Process image file.
    
    Args:
        image_path: Path to image file
        debug: Enable debug output
        
    Returns:
        Success state
    """
    # Create coordinator
    coordinator = ProcessingCoordinator()
    
    # Process image
    results = coordinator.process_tape(image_path, debug=debug)
    
    if not results["success"]:
        print(f"Error: {results['error']}", file=sys.stderr)
        return False
        
    # Print vision data
    vision_data = results["vision_data"]
    print("\nVision Data:")
    print(f"Image Size: {vision_data['image_size']}")
    print(f"Sharpness: {vision_data['sharpness']:.1f}")
    print(f"Rectangles: {vision_data['rectangles']}")
    print(f"Text Regions: {vision_data['text_regions']}")
    print(f"Processing Time: {vision_data['processing_time']:.2f}s")
    
    # Print extracted titles
    print("\nExtracted Titles:")
    if results["extracted_titles"]:
        for title in results["extracted_titles"]:
            print(f"- {title}")
    else:
        print("No titles extracted")
        
    # Print movie data
    print("\nMovie Data:")
    if "movie_data" in results:
        movie = results["movie_data"]
        print(f"Title: {movie['title']}")
        
        if "release_date" in movie:
            print(f"Year: {movie['release_date'][:4]}")
            
        if "vote_average" in movie:
            print(f"Rating: {movie['vote_average']:.1f}/10")
            
        if "genres" in movie and movie["genres"]:
            genres = [g["name"] for g in movie["genres"]]
            print(f"Genres: {', '.join(genres)}")
            
        if "overview" in movie:
            print(f"\nOverview:\n{movie['overview']}")
    else:
        print("No movie data found")
        
    # Print debug info
    if debug and "debug_image" in results:
        print(f"\nDebug image saved to: {results['debug_image']}")
        
    # Print results path
    if "results_path" in results:
        print(f"\nResults saved to: {results['results_path']}")
        
    return True

def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Process VHS tape images."
    )
    
    parser.add_argument(
        "image",
        help="Path to image file"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    args = parser.parse_args()
    
    try:
        # Setup logging
        setup_logging()
        
        # Validate settings
        validate_settings()
        
        # Process image
        if process_image(args.image, args.debug):
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
        
if __name__ == "__main__":
    sys.exit(main())
