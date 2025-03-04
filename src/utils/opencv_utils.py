"""
OpenCV utility functions.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

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

def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert image to grayscale if needed."""
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        return gray
    except Exception as e:
        logger.error(f"Grayscale conversion error: {e}")
        return image
        
def resize_image(image: np.ndarray, target_width: int = 1024) -> np.ndarray:
    """Resize image maintaining aspect ratio."""
    try:
        h, w = image.shape[:2]
        if w > target_width:
            ratio = target_width / w
            new_size = (target_width, int(h * ratio))
            resized = cv2.resize(image, new_size)
            return resized
        return image
    except Exception as e:
        logger.error(f"Resize error: {e}")
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

def denoise_image(image: np.ndarray) -> np.ndarray:
    """
    Apply multi-stage denoising to image.
    
    Args:
        image: Input grayscale or color image
        
    Returns:
        Denoised image
    """
    try:
        # Ensure uint8 type
        if image.dtype != np.uint8:
            image = cv2.convertScaleAbs(image)
        
        # First pass: Mild bilateral filtering for edge preservation
        bilateral = cv2.bilateralFilter(image, d=5, sigmaColor=25, sigmaSpace=25)
        
        # Second pass: Non-local means for fine detail preservation
        if len(image.shape) == 2:
            # For grayscale images
            # Use moderate h value and small windows for detail preservation
            denoised = cv2.fastNlMeansDenoising(
                bilateral,
                None,
                h=7,  # Moderate strength
                templateWindowSize=5,  # Small template for detail
                searchWindowSize=15  # Moderate search area
            )
        else:
            # For color images
            # Use different strengths for luminance and color
            denoised = cv2.fastNlMeansDenoisingColored(
                bilateral,
                None,
                h=7,  # Luminance filtering
                hColor=10,  # Color filtering
                templateWindowSize=5,
                searchWindowSize=15
            )
            
        # Final pass: Light gaussian blur to smooth any remaining artifacts
        # but only if the image has high frequency noise
        if np.std(denoised) > np.std(bilateral):
            denoised = cv2.GaussianBlur(denoised, (3,3), 0.5)
            
        return denoised
    except Exception as e:
        logger.error(f"Denoising error: {e}")
        return image

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image optimized for text extraction.
    
    Args:
        image: Input image array
        
    Returns:
        Preprocessed image array optimized for OCR
    """
    try:
        # Convert to grayscale
        gray = convert_to_grayscale(image)
        
        # Resize while maintaining text readability
        resized = resize_image(gray, target_width=1600)  # Higher resolution for better text detail
        
        # Initial denoising to clean up the image
        denoised = denoise_image(resized)
        
        # Enhance local contrast for better text definition
        enhanced = enhance_contrast(denoised)
        
        # Normalize image statistics for consistent processing
        normalized = normalize_image(enhanced, target_mean=127, target_std=40)
        
        # Second pass of targeted denoising with text preservation
        if np.std(normalized) > 45:  # Only if image is still noisy
            final = cv2.bilateralFilter(normalized, d=5, sigmaColor=10, sigmaSpace=10)
        else:
            final = normalized
            
        return final
        
    except Exception as e:
        logger.error(f"Preprocessing error: {e}")
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
