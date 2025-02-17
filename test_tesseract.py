"""
Tesseract OCR test script.
"""
import argparse
import logging
import sys
from pathlib import Path

import cv2
import numpy as np
import pytesseract

from src.config.settings import VISION_SETTINGS
from src.utils.opencv_utils import enhance_image

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def test_tesseract_version():
    """Test Tesseract version."""
    try:
        version = pytesseract.get_tesseract_version()
        print(f"\nTesseract Version: {version}")
        return True
        
    except Exception as e:
        print(f"\nError getting Tesseract version: {e}")
        return False

def test_tesseract_cmd():
    """Test Tesseract command."""
    try:
        cmd = VISION_SETTINGS["tesseract_cmd"]
        if cmd:
            print(f"\nTesseract Command: {cmd}")
            pytesseract.pytesseract.tesseract_cmd = cmd
            return True
            
        print("\nTesseract command not configured")
        return False
        
    except Exception as e:
        print(f"\nError configuring Tesseract command: {e}")
        return False

def test_image_ocr(image_path: str, debug: bool = False):
    """
    Test OCR on image.
    
    Args:
        image_path: Path to test image
        debug: Enable debug output
    """
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise RuntimeError(f"Failed to load image: {image_path}")
            
        print(f"\nProcessing: {image_path}")
        print(f"Image Size: {image.shape[1]}x{image.shape[0]}")
        
        # Enhance image
        enhanced = enhance_image(
            image,
            sharpen=VISION_SETTINGS["sharpen"],
            contrast=VISION_SETTINGS["enhance_contrast"],
            denoise=VISION_SETTINGS["denoise"]
        )
        
        # Extract text
        print("\nExtracting text...")
        text = pytesseract.image_to_string(
            enhanced,
            config=VISION_SETTINGS["tesseract_config"]
        )
        
        if text.strip():
            print("\nExtracted Text:")
            print("-" * 40)
            print(text.strip())
            print("-" * 40)
        else:
            print("\nNo text extracted")
            
        if debug:
            # Get confidence data
            print("\nConfidence Data:")
            data = pytesseract.image_to_data(
                enhanced,
                config=VISION_SETTINGS["tesseract_config"],
                output_type=pytesseract.Output.DICT
            )
            
            for i, conf in enumerate(data["conf"]):
                if conf > 0:  # Filter empty results
                    text = data["text"][i]
                    print(f"Text: {text:<20} Confidence: {conf:>6.2f}%")
                    
            # Save debug image
            debug_path = str(Path(image_path).with_suffix(".debug.jpg"))
            cv2.imwrite(debug_path, enhanced)
            print(f"\nDebug image saved: {debug_path}")
            
    except Exception as e:
        print(f"\nError processing image: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Tesseract OCR setup")
    parser.add_argument(
        "image",
        nargs="?",
        help="Path to test image"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Test Tesseract installation
    print("\nTesting Tesseract Installation")
    print("-" * 40)
    
    if not test_tesseract_version():
        return 1
        
    if not test_tesseract_cmd():
        return 1
        
    # Test image processing
    if args.image:
        test_image_ocr(args.image, args.debug)
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
