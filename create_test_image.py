"""
Test image generator script.
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

def create_test_image(
    title: str,
    year: str = None,
    size: tuple = (640, 480),
    background_color: tuple = (255, 255, 255),
    text_color: tuple = (0, 0, 0),
    font_scale: float = 1.0,
    thickness: int = 2,
    border_size: int = 20,
    output_path: str = None
) -> str:
    """
    Create test VHS cover image.
    
    Args:
        title: Movie title
        year: Release year
        size: Image dimensions (width, height)
        background_color: Background color (B, G, R)
        text_color: Text color (B, G, R)
        font_scale: Font size scale
        thickness: Text thickness
        border_size: Border thickness
        output_path: Output file path
        
    Returns:
        Path to created image
    """
    try:
        # Create image
        image = np.full(
            (size[1], size[0], 3),
            background_color,
            dtype=np.uint8
        )
        
        # Draw border
        cv2.rectangle(
            image,
            (border_size, border_size),
            (size[0] - border_size, size[1] - border_size),
            text_color,
            thickness
        )
        
        # Format text
        if year:
            text = f"{title} ({year})"
        else:
            text = title
            
        # Calculate text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(
            text,
            font,
            font_scale,
            thickness
        )[0]
        
        # Calculate position
        x = int((size[0] - text_size[0]) / 2)
        y = int((size[1] + text_size[1]) / 2)
        
        # Draw text
        cv2.putText(
            image,
            text,
            (x, y),
            font,
            font_scale,
            text_color,
            thickness
        )
        
        # Create output path
        if output_path is None:
            output_path = f"test_vhs_cover.jpg"
            
        # Create directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save image
        cv2.imwrite(output_path, image)
        
        return output_path
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Create test VHS cover images."
    )
    
    parser.add_argument(
        "title",
        help="Movie title"
    )
    
    parser.add_argument(
        "year",
        nargs="?",
        help="Release year"
    )
    
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path"
    )
    
    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="Image width"
    )
    
    parser.add_argument(
        "--height",
        type=int,
        default=480,
        help="Image height"
    )
    
    parser.add_argument(
        "--font-scale",
        type=float,
        default=1.0,
        help="Font size scale"
    )
    
    args = parser.parse_args()
    
    # Create image
    output_path = create_test_image(
        args.title,
        args.year,
        size=(args.width, args.height),
        font_scale=args.font_scale,
        output_path=args.output
    )
    
    if output_path:
        print(f"Image saved to: {output_path}")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
