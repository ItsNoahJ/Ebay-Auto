"""
OpenCV utility functions.
"""
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

def load_image(path: str) -> Optional[np.ndarray]:
    """
    Load image from path.
    
    Args:
        path: Path to image file
        
    Returns:
        Image array or None if loading fails
    """
    try:
        image = cv2.imread(path)
        if image is None:
            logger.error(f"Failed to load image: {path}")
            return None
            
        return image
    except Exception as e:
        logger.error(f"Error loading image {path}: {e}")
        return None

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for text extraction.
    
    Args:
        image: Input image array
        
    Returns:
        Preprocessed image array
    """
    try:
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Apply CLAHE for adaptive contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast_enhanced = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(contrast_enhanced)
        
        # Adaptive threshold with original parameters
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Original block size
            2    # Original C parameter
        )
        
        return binary
        
    except Exception as e:
        logger.error(f"Preprocessing error: {e}")
        return image

def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast using CLAHE.
    
    Args:
        image: Input grayscale image
        
    Returns:
        Contrast enhanced image
    """
    try:
        # Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(image)
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Contrast enhancement error: {e}")
        return image

def normalize_image(image: np.ndarray, target_mean: float = 127, target_std: float = 50) -> np.ndarray:
    """
    Normalize image with advanced histogram matching.
    
    Args:
        image: Input image array
        target_mean: Target mean intensity
        target_std: Target standard deviation
        
    Returns:
        Normalized image array
    """
    try:
        # Calculate current statistics
        mean = np.mean(image)
        std = np.std(image)
        
        # Normalize to target statistics
        normalized = ((image - mean) * (target_std / std) + target_mean)
        normalized = np.clip(normalized, 0, 255).astype(np.uint8)
        
        return normalized
        
    except Exception as e:
        logger.error(f"Normalization error: {e}")
        return image

def extract_text_regions(image: np.ndarray) -> list:
    """
    Extract potential text regions from image.
    
    Args:
        image: Input image array
        
    Returns:
        List of (x,y,w,h) region tuples
    """
    try:
        # Find contours
        contours, _ = cv2.findContours(
            image,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Get bounding rectangles
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter small regions
            if w > 20 and h > 20:
                regions.append((x, y, w, h))
                
        return regions
        
    except Exception as e:
        logger.error(f"Region extraction error: {e}")
        return []
