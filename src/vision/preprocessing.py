"""
Vision preprocessing pipeline components.
"""
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional
import re

import cv2
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class TextRegion:
    """Represents a detected text region in the image."""
    x: int
    y: int 
    width: int
    height: int
    image: np.ndarray
    confidence: float = 0.0
    text: str = ""

    def to_bbox(self) -> Tuple[int, int, int, int]:
        """Convert to (x, y, w, h) format."""
        return (self.x, self.y, self.width, self.height)

class FastCLAHE:
    """Optimized CLAHE implementation."""
    
    def __init__(self, clip_limit: float = 1.5, tile_size: Tuple[int, int] = (4, 4)):
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)
        
    def process(self, image: Optional[np.ndarray]) -> np.ndarray:
        """Apply CLAHE to image."""
        try:
            if image is None or not isinstance(image, np.ndarray) or image.size == 0:
                raise ValueError("Invalid image input")
                
            if len(image.shape) == 3:
                # Convert to LAB color space for better contrast enhancement
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                
                # Apply CLAHE to L channel
                cl = self.clahe.apply(l)
                
                # Merge channels and convert back
                enhanced_lab = cv2.merge((cl, a, b))
                return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
            elif len(image.shape) == 2:
                # Grayscale image
                return self.clahe.apply(image)
            else:
                raise ValueError(f"Invalid image shape: {image.shape}")
        except Exception as e:
            logger.error(f"CLAHE processing error: {e}")
            return image if isinstance(image, np.ndarray) else np.array([])

class BilateralFilter:
    """Edge-preserving bilateral filter."""
    
    def __init__(self, d: int = 7, sigma_color: float = 50, sigma_space: float = 50):
        self.d = d
        self.sigma_color = sigma_color
        self.sigma_space = sigma_space
        
    def process(self, image: Optional[np.ndarray]) -> np.ndarray:
        """Apply bilateral filter to image."""
        try:
            if image is None or not isinstance(image, np.ndarray) or image.size == 0:
                raise ValueError("Invalid image input")
                
            if not (len(image.shape) == 2 or 
                   (len(image.shape) == 3 and image.shape[2] in [1, 3, 4])):
                raise ValueError(f"Invalid image shape: {image.shape}")
                
            return cv2.bilateralFilter(
                image, 
                self.d,
                self.sigma_color,
                self.sigma_space
            )
        except Exception as e:
            logger.error(f"Bilateral filter error: {e}")
            return image if isinstance(image, np.ndarray) else np.array([])

class RegionDetector:
    """Text region detection using contour analysis."""
    
    def __init__(
        self,
        min_area: int = 100,  # Reduced from 200
        min_width: int = 10,  # New minimum width threshold
        min_height: int = 10,  # New minimum height threshold
        min_aspect: float = 0.1,
        max_aspect: float = 10.0
    ):
        self.min_area = min_area
        self.min_width = min_width
        self.min_height = min_height
        self.min_aspect = min_aspect
        self.max_aspect = max_aspect
        
    def detect(self, image: Optional[np.ndarray]) -> List[TextRegion]:
        """
        Detect potential text regions in image.
        
        Args:
            image: Preprocessed binary image
            
        Returns:
            List of TextRegion objects
        """
        try:
            if image is None or not isinstance(image, np.ndarray) or image.size == 0:
                raise ValueError("Invalid image input")
                
            if len(image.shape) != 2:
                raise ValueError("Input must be binary/grayscale image")
            
            # Ensure binary image
            if image.dtype != np.uint8:
                image = image.astype(np.uint8)
            
            # Find contours
            contours, _ = cv2.findContours(
                image,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            regions = []
            for contour in contours:
                try:
                    x, y, w, h = cv2.boundingRect(contour)
                    area = w * h
                    aspect = w / h if h > 0 else 0
                    
                    # Filter regions based on size, dimensions and aspect ratio
                    if (area >= self.min_area and 
                        w >= self.min_width and 
                        h >= self.min_height and
                        self.min_aspect <= aspect <= self.max_aspect):
                        
                        # Validate region bounds
                        if (y >= 0 and y + h <= image.shape[0] and
                            x >= 0 and x + w <= image.shape[1]):
                            
                            # Extract region image
                            region_img = image[y:y+h, x:x+w].copy()
                            
                            regions.append(TextRegion(
                                x=x,
                                y=y,
                                width=w,
                                height=h,
                                image=region_img
                            ))
                except Exception as region_error:
                    logger.warning(f"Failed to process region: {region_error}")
                    continue
                    
            return regions
            
        except Exception as e:
            logger.error(f"Region detection error: {e}")
            return []

class PreprocessingPipeline:
    """Fast image preprocessing pipeline."""
    
    def __init__(
        self,
        clahe: Optional[FastCLAHE] = None,
        bilateral: Optional[BilateralFilter] = None,
        detector: Optional[RegionDetector] = None
    ):
        self.clahe = clahe or FastCLAHE()
        self.bilateral = bilateral or BilateralFilter()
        self.detector = detector or RegionDetector()
        
    def preprocess(self, image: Optional[np.ndarray]) -> Tuple[np.ndarray, List[TextRegion]]:
        """
        Preprocess image and detect text regions.
        
        Args:
            image: Input image array
            
        Returns:
            Tuple of (preprocessed image, list of text regions)
        """
        try:
            # Validate input
            if image is None or not isinstance(image, np.ndarray) or image.size == 0:
                logger.error("Invalid input image")
                return np.array([]), []
                
            if not (len(image.shape) == 2 or 
                   (len(image.shape) == 3 and image.shape[2] in [1, 3, 4])):
                logger.error(f"Invalid image shape: {image.shape}")
                return image, []
            
            # Convert to grayscale if needed
            try:
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image.copy()
            except Exception as e:
                logger.error(f"Grayscale conversion failed: {e}")
                return image, []
                
            # Apply preprocessing steps
            try:
                enhanced = self.clahe.process(gray)
                if enhanced.size == 0:  # CLAHE failed
                    return image, []
                    
                filtered = self.bilateral.process(enhanced)
                if filtered.size == 0:  # Bilateral filter failed
                    return image, []
                
                # Binarize
                try:
                    binary = cv2.adaptiveThreshold(
                        filtered,
                        255,
                        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                        cv2.THRESH_BINARY,
                        11,
                        2
                    )
                except Exception as e:
                    logger.error(f"Binarization failed: {e}")
                    return image, []
                    
                # Clean up noise with morphological operations
                try:
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
                    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
                except Exception as e:
                    logger.error(f"Morphological operation failed: {e}")
                    return binary, []  # Return binary image if cleanup fails
                
                # Detect text regions
                regions = self.detector.detect(cleaned)
                
                return cleaned, regions
                
            except Exception as e:
                logger.error(f"Preprocessing step failed: {e}")
                return image, []
            
        except Exception as e:
            logger.error(f"Preprocessing pipeline error: {e}")
            if isinstance(image, np.ndarray):
                return image, []
            return np.array([]), []

class ConfidenceScorer:
    """Quick pattern-based confidence scoring."""
    
    def __init__(self):
        # Common patterns for different text categories
        self.patterns = {
            "title": [
                r"^[A-Z]",  # Starts with capital letter
                r"^[A-Za-z0-9'\- ]{2,50}$",  # Valid length and chars
                r"^(?:The |A )",  # Common article prefixes
                r"(?:II|III|IV|V|VI)$",  # Roman numerals
                r"\sand\s",  # Common conjunction
                r"[!:']"  # Common title punctuation
            ],
            "year": [
                r"^(?:19[7-9]\d|200[0-6])$"  # VHS era years (1970-2006)
            ],
            "runtime": [
                r"^\d{2,3}$",  # 2-3 digit number
                r"^(?:6\d|7\d|8\d|9\d|1[0-4]\d|150)$"  # 60-150 minutes
            ],
            "rating": [
                r"^(?:G|PG|PG-13|R|NC-17)$"  # Valid MPAA ratings
            ],
            "studio": [
                r"(?i)pictures?$",  # Pictures/Picture
                r"(?i)films?$",  # Films/Film
                r"(?i)(?:entertainment|studios?|productions?|media)$"  # Other common suffixes
            ],
            "director": [
                r"(?i)^directed by ",  # Director prefix
                r"^[A-Z][a-z]+ [A-Z][a-z]+$",  # First Last name pattern
                r"^[A-Z]\. [A-Z][a-z]+$"  # Initial. Last name pattern
            ],
            "cast": [
                r"(?i)^(?:starring|with|featuring) ",  # Cast intro phrases
                r"(?:[A-Z][a-z]+ [A-Z][a-z]+(?:,\s*)?)+$"  # Name list pattern
            ]
        }
        
    def score_text(self, text: str, category: str) -> float:
        """
        Calculate confidence score for extracted text.
        
        Args:
            text: Extracted text
            category: Text category (title, year, etc.)
            
        Returns:
            Confidence score 0-100
        """
        if not text or category not in self.patterns:
            return 0.0
            
        # Clean input text
        text = text.strip()
        if not text:
            return 0.0
            
        # Start with lower base score
        score = 30.0
        patterns = self.patterns[category]
        
        # Length validation first
        if category == "title":
            if len(text) < 2:
                return 20.0  # Very short titles are suspicious
            elif len(text) <= 50:
                score += 20.0  # Reasonable length bonus
            if text.isupper():  # All caps titles are suspicious
                score -= 20.0
        
        # Category-specific scoring
        if category == "year":
            # Year must be exactly 4 digits in VHS era
            if re.match(patterns[0], text):
                score = 100.0
            else:
                # Check if it's at least a 4-digit year
                if re.match(r"^\d{4}$", text):
                    year = int(text)
                    if 1960 <= year <= 2010:  # Close to VHS era
                        score = 70.0
                    else:
                        score = 30.0
                        
        elif category == "rating":
            # Rating must exactly match MPAA ratings
            if re.match(patterns[0], text.upper()):
                score = 100.0
            else:
                score = 0.0
                
        elif category == "runtime":
            # Runtime must be in valid range
            if re.match(patterns[1], text):  # Common lengths
                score = 100.0
            elif re.match(patterns[0], text):  # Valid number
                minutes = int(text)
                if 30 <= minutes <= 240:  # Extended range
                    score = 70.0
                else:
                    score = 30.0
                    
        else:
            # General pattern matching for other categories
            matches = sum(bool(re.search(p, text)) for p in patterns)
            if matches:
                # More matches = higher confidence
                score += (50.0 * matches / len(patterns))
                
            # Special cases
            if category == "director" and "directed by" in text.lower():
                score += 20.0
            elif category == "cast" and "," in text:
                score += 20.0
            elif category == "studio" and any(x in text.lower() for x in ["studios", "pictures", "films"]):
                score += 20.0
                
        return min(max(score, 0.0), 100.0)
