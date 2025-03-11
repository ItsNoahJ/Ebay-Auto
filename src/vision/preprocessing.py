"""
Preprocessing pipeline for optimized OCR and text extraction.
"""
import logging
import time
from typing import List, Tuple, Optional, Callable

class TimeoutError(Exception):
    """Exception raised when an operation times out."""
    pass

from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable

import cv2
import numpy as np

from src.utils.opencv_utils import (
    convert_to_grayscale,
    resize_image,
    denoise_image,
    enhance_contrast,
    normalize_image
)

logger = logging.getLogger(__name__)

@dataclass
class TextRegion:
    """Represents a detected text region in an image."""
    x: int
    y: int
    width: int
    height: int
    image: Optional[np.ndarray] = None
    confidence: float = 0.0

class FastCLAHE:
    """Fast Contrast Limited Adaptive Histogram Equalization."""
    
    def __init__(self, clip_limit: float = 2.0, grid_size: Tuple[int, int] = (8, 8)):
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
        
    def process(self, image: np.ndarray) -> np.ndarray:
        """Apply CLAHE to grayscale image."""
        try:
            if len(image.shape) > 2:
                image = convert_to_grayscale(image)
            return self.clahe.apply(image)
        except Exception as e:
            logger.error(f"CLAHE processing failed: {e}")
            return image

class BilateralFilter:
    """Edge-preserving bilateral filter."""
    
    def __init__(self, d: int = 5, sigma_color: float = 25, sigma_space: float = 25):
        self.d = d
        self.sigma_color = sigma_color
        self.sigma_space = sigma_space
        
    def process(self, image: np.ndarray) -> np.ndarray:
        """Apply bilateral filtering."""
        try:
            return cv2.bilateralFilter(
                image,
                d=self.d,
                sigmaColor=self.sigma_color,
                sigmaSpace=self.sigma_space
            )
        except Exception as e:
            logger.error(f"Bilateral filtering failed: {e}")
            return image

class RegionDetector:
    """Text region detector optimized for VHS covers."""
    
    def __init__(
        self,
        min_area: int = 50,  # Lower minimum area to catch smaller text
        max_area_ratio: float = 0.8,  # Allow larger regions
        min_aspect: float = 0.05,  # Allow narrower regions
        max_aspect: float = 20.0  # Allow wider regions
    ):
        self.min_area = min_area
        self.max_area_ratio = max_area_ratio
        self.min_aspect = min_aspect
        self.max_aspect = max_aspect
        
    def detect(self, image: np.ndarray) -> List[TextRegion]:
        """
        Detect potential text regions in image.
        
        Args:
            image: Preprocessed grayscale image
            
        Returns:
            List of TextRegion objects
        """
        try:
            # Get image dimensions
            height, width = image.shape[:2]
            max_area = int(width * height * self.max_area_ratio)
            
            # Create binary image with more aggressive thresholding
            # Since test image has black text on white background, we invert
            blur = cv2.GaussianBlur(image, (5, 5), 0)
            _, binary = cv2.threshold(
                blur,
                0,
                255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            
            # Apply morphological operations to connect text components
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            # Clean up noise
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(
                binary,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            regions = []
            for contour in contours:
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect = w / float(h)
                
                # Filter regions
                if (
                    area >= self.min_area
                    and area <= max_area
                    and self.min_aspect <= aspect <= self.max_aspect
                ):
                    # Extract region image
                    margin = 5  # Add small margin
                    x1 = max(0, x - margin)
                    y1 = max(0, y - margin)
                    x2 = min(width, x + w + margin)
                    y2 = min(height, y + h + margin)
                    
                    region_img = image[y1:y2, x1:x2].copy()
                    
                    regions.append(TextRegion(
                        x=x1,
                        y=y1,
                        width=x2-x1,
                        height=y2-y1,
                        image=region_img
                    ))
                    
            return regions
            
        except Exception as e:
            logger.error(f"Region detection failed: {e}")
            return []

class ConfidenceScorer:
    """Confidence scoring for extracted text."""
    
    def score_text(self, text: str, category: str) -> float:
        """
        Score confidence of extracted text based on category.
        
        Args:
            text: Extracted text
            category: Text category (title, year, etc)
            
        Returns:
            Confidence score 0-100
        """
        if not text:
            return 0.0
            
        try:
            base_score = 60.0  # Start with base confidence
            
            # Category-specific scoring
            if category == "year":
                # Year should be 4 digits between 1950-2025
                if text.isdigit() and len(text) == 4:
                    year = int(text)
                    if 1950 <= year <= 2025:
                        base_score = 90.0
                    
            elif category == "runtime":
                # Runtime should be digits only
                if text.isdigit():
                    runtime = int(text)
                    if 60 <= runtime <= 240:  # Most movies 1-4 hours
                        base_score = 85.0
                        
            elif category == "rating":
                # Rating should match known values
                ratings = {"G", "PG", "PG-13", "R", "NC-17"}
                if text.upper() in ratings:
                    base_score = 95.0
                    
            # Length-based adjustments
            if len(text) < 2:
                base_score *= 0.5
            elif len(text) > 100:
                base_score *= 0.7
                
            return min(100.0, base_score)
            
        except Exception as e:
            logger.error(f"Confidence scoring failed: {e}")
            return 0.0

class PreprocessingPipeline:
    """Complete preprocessing pipeline for text extraction."""
    
    def __init__(self):
        self.clahe = FastCLAHE(clip_limit=2.0, grid_size=(8,8))
        self.bilateral = BilateralFilter()
        self.intermediate_images = {}
        
    def preprocess(
        self, 
        image: np.ndarray
    ) -> np.ndarray:
        """
        Preprocess image for text extraction.
        
        Args:
            image: Input image array
            
        Returns:
            Preprocessed image array
        """
        try:
            # Store original
            self.intermediate_images["Original"] = image.copy()

            # Convert to grayscale
            gray = convert_to_grayscale(image)
            self.intermediate_images["grayscale"] = gray.copy()
            
            # Resize for consistent processing
            resized = resize_image(gray, target_width=1600)
            
            # Denoise
            denoised = denoise_image(resized)
            
            # CLAHE enhancement
            enhanced = self.clahe.process(denoised)
            self.intermediate_images["enhance"] = enhanced.copy()
            
            # Normalize
            normalized = normalize_image(enhanced, target_mean=127, target_std=40)
            
            # Apply bilateral filtering if needed
            img_std = np.std(normalized)
            if img_std > 45:
                final = self.bilateral.process(normalized)
            else:
                final = normalized
                
            self.intermediate_images["text"] = final.copy()
            return final
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            self.intermediate_images.clear()
            return image  # Return original image on error
