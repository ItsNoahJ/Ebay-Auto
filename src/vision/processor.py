"""
Vision processing module.
"""
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pytesseract

from ..config.settings import STORAGE_PATHS, VISION_SETTINGS
from ..utils.opencv_utils import (
    detect_edges,
    detect_rectangles,
    detect_text_regions,
    draw_debug_image,
    enhance_image,
    resize_image
)

class VisionProcessor:
    """Vision processor for VHS tapes."""
    
    def __init__(self):
        """Initialize processor."""
        self.logger = logging.getLogger(__name__)
        
        # Configure Tesseract
        if VISION_SETTINGS["tesseract_cmd"]:
            pytesseract.pytesseract.tesseract_cmd = (
                VISION_SETTINGS["tesseract_cmd"]
            )
            
    def calculate_sharpness(self, image: np.ndarray) -> float:
        """
        Calculate image sharpness.
        
        Args:
            image: Input image
            
        Returns:
            Sharpness score
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Calculate Laplacian variance
        return cv2.Laplacian(gray, cv2.CV_64F).var()
        
    def preprocess_image(
        self,
        image: np.ndarray
    ) -> Tuple[np.ndarray, Dict]:
        """
        Preprocess image.
        
        Args:
            image: Input image
            
        Returns:
            Tuple of (processed image, metadata)
        """
        # Calculate size
        height, width = image.shape[:2]
        
        # Calculate sharpness
        sharpness = self.calculate_sharpness(image)
        
        # Resize if needed
        target_width = VISION_SETTINGS["target_width"]
        
        if width > target_width:
            image = resize_image(image, width=target_width)
            
        # Create metadata
        data = {
            "image_size": f"{width}x{height}",
            "sharpness": sharpness
        }
        
        return image, data
        
    def capture_regions(
        self,
        image: np.ndarray
    ) -> List[Dict]:
        """
        Capture text regions.
        
        Args:
            image: Input image
            
        Returns:
            List of region data
        """
        # Detect edges
        edges = detect_edges(image)
        
        # Detect rectangles
        rectangles = detect_rectangles(
            edges,
            min_area=VISION_SETTINGS["min_cover_area"],
            max_area=int(
                image.shape[0] * image.shape[1] *
                VISION_SETTINGS["max_cover_area_ratio"]
            ),
            epsilon_factor=VISION_SETTINGS["epsilon_factor"]
        )
        
        # Process each rectangle
        regions = []
        
        for rect in rectangles:
            # Create mask
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            cv2.drawContours(mask, [rect], -1, 255, -1)
            
            # Extract region
            region = cv2.bitwise_and(image, image, mask=mask)
            
            # Detect text regions
            boxes = detect_text_regions(
                region,
                block_size=VISION_SETTINGS["text_block_size"],
                c=VISION_SETTINGS["text_c"]
            )
            
            # Extract text
            texts = []
            
            for x, y, w, h in boxes:
                # Get text region
                text_region = region[y:y+h, x:x+w]
                
                # Enhance region
                enhanced = enhance_image(text_region)
                
                # Extract text
                text = pytesseract.image_to_string(
                    enhanced,
                    config=VISION_SETTINGS["tesseract_config"]
                )
                
                if text.strip():
                    texts.append(text.strip())
                    
            # Create region data
            if texts:
                regions.append({
                    "coords": rect.tolist(),
                    "text": "\n".join(texts)
                })
                
        return regions
        
    def process_image(
        self,
        image_path: str,
        debug: bool = False
    ) -> Dict:
        """
        Process image file.
        
        Args:
            image_path: Path to image file
            debug: Enable debug output
            
        Returns:
            Processing results
        """
        try:
            # Start timing
            start_time = time.time()
            
            # Load image
            image = cv2.imread(image_path)
            
            if image is None:
                raise RuntimeError(f"Failed to load image: {image_path}")
                
            # Preprocess image
            image, data = self.preprocess_image(image)
            
            # Capture regions
            regions = self.capture_regions(image)
            
            # Create results
            texts = []
            for region in regions:
                texts.append(region["text"])
                
            # Add data
            data.update({
                "rectangles": len(regions),
                "text_regions": sum(
                    1 for r in regions if r["text"]
                ),
                "processing_time": time.time() - start_time
            })
            
            results = {
                "success": True,
                "texts": texts,
                "vision_data": data
            }
            
            # Add debug data
            if debug:
                debug_path = str(
                    STORAGE_PATHS["debug"] /
                    Path(image_path).with_suffix(".debug.jpg").name
                )
                
                # Create directory
                Path(debug_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Create debug image
                debug_image = draw_debug_image(image, regions)
                
                # Save debug image
                cv2.imwrite(debug_path, debug_image)
                
                results["debug_image"] = debug_path
                
            return results
            
        except Exception as e:
            self.logger.exception("Processing error")
            return {
                "success": False,
                "error": str(e)
            }
