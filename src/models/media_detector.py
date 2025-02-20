"""
Media type detection and classification.
"""
import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import json
import os

class MediaDetector:
    """Detects and classifies different types of physical media."""
    
    def __init__(self, config_path: str = "config/media_features.json"):
        """Initialize the media detector."""
        self.media_types = {}
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Convert lists to tuples for immutability
                    for media_type, props in config.items():
                        self.media_types[media_type] = {
                            'aspect_ratio_range': tuple(props['aspect_ratio_range']),
                            'features': {
                                'text_regions': [tuple(region) for region in props['features']['text_regions']],
                                'color_ranges': [tuple(map(tuple, color_range)) for color_range in props['features']['color_ranges']]
                            }
                        }
            else:
                print(f"Warning: Configuration file not found at {config_path}")
        except Exception as e:
            print(f"Error loading configuration: {e}")
            # Fallback to default configuration
            self.media_types = {
                'vhs': {
                    'aspect_ratio_range': (1.4, 1.8),
                    'features': {
                        'text_regions': [(0.05, 0.02, 0.95, 0.3),  # Title
                                       (0.1, 0.25, 0.45, 0.45),   # Year
                                       (0.55, 0.25, 0.9, 0.45)],  # Runtime
                        'color_ranges': [
                            ((0, 0, 0), (180, 50, 100)),      # Black
                            ((0, 0, 150), (180, 30, 255)),    # White
                            ((0, 0, 0), (180, 20, 80))        # Dark regions
                        ]
                    }
                }
            }
    
    def detect_media_type(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Detect the type of media in the image.
        
        Args:
            image: OpenCV image array
            
        Returns:
            Tuple of (media_type, confidence_score)
        """
        scores = {}
        
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Get image dimensions and aspect ratio
        height, width = image.shape[:2]
        aspect_ratio = width / height
        
        for media_type, properties in self.media_types.items():
            score = 0
            max_score = 0
            
            # Check aspect ratio (max 45 points) - Increased weight
            ar_min, ar_max = properties['aspect_ratio_range']
            if ar_min <= aspect_ratio <= ar_max:
                # Calculate how close we are to the ideal aspect ratio
                ideal_ratio = (ar_min + ar_max) / 2
                deviation = abs(aspect_ratio - ideal_ratio) / ideal_ratio
                # Steeper penalty for deviation from ideal ratio
                ar_score = 45 * max(0, 1 - (deviation * 3))
                score += ar_score
            max_score += 45
            
            # Check color distribution (max 30 points) - Decreased weight
            color_score = 0
            for color_range in properties['features']['color_ranges']:
                mask = cv2.inRange(hsv, np.array(color_range[0]), np.array(color_range[1]))
                color_ratio = cv2.countNonZero(mask) / (height * width)
                # More precise color matching
                if color_ratio > 0.05:  # Minimum threshold to count
                    color_score += min(color_ratio * 120, 10)  # Up to 10 points per color range
            score += color_score
            max_score += 30
            
            # Check for text regions (max 25 points) - Adjusted weight and improved detection
            text_score = 0
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Apply contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            for region in properties['features']['text_regions']:
                x1 = int(width * region[0])
                y1 = int(height * region[1])
                x2 = int(width * region[2])
                y2 = int(height * region[3])
                
                roi = gray[y1:y2, x1:x2]
                
                # Multi-scale edge detection with better sensitivity
                edges1 = cv2.Canny(roi, 30, 100)   # Very sensitive for faint text
                edges2 = cv2.Canny(roi, 50, 150)   # Medium sensitivity
                edges3 = cv2.Canny(roi, 100, 200)  # Original sensitivity
                edges = cv2.bitwise_or(cv2.bitwise_or(edges1, edges2), edges3)
                
                # Look for structured patterns (text-like features)
                kernel = np.ones((3,3), np.uint8)
                dilated = cv2.dilate(edges, kernel, iterations=1)
                text_pixels = cv2.countNonZero(dilated)
                roi_area = (y2-y1) * (x2-x1)
                
                if roi_area > 0:
                    density = text_pixels / roi_area
                    # Refined scoring based on typical text density ranges
                    if 0.05 <= density <= 0.5:  # Wider acceptable range
                        if 0.1 <= density <= 0.3:  # Optimal range
                            text_score += min(density * 100, 8.33)  # Up to 8.33 points per region (25/3)
                        else:
                            text_score += min(density * 50, 4)  # Reduced score for less optimal densities
            
            score += text_score
            max_score += 25
            
            # Calculate final confidence score (0-100) with minimum threshold
            raw_score = (score / max_score) * 100
            
            # Apply confidence threshold and media-specific adjustments
            if raw_score < 40:  # Minimum threshold
                scores[media_type] = 0
            else:
                # Apply media-specific adjustments based on key characteristics
                if media_type == 'vhs':
                    if ar_min <= aspect_ratio <= ar_max:
                        raw_score *= 1.25  # Strong boost for VHS with correct ratio
                    if aspect_ratio < 1.2:  # VHS shouldn't be too square
                        raw_score *= 0.6
                elif media_type == 'dvd':
                    if aspect_ratio > 1.4:  # DVDs are typically more vertical
                        raw_score *= 0.7
                    if 0.68 <= aspect_ratio <= 0.76:  # Perfect DVD ratio range
                        raw_score *= 1.2
                elif media_type == 'cd':
                    if abs(aspect_ratio - 1.0) < 0.1:  # CD cases are nearly square
                        raw_score *= 1.2
                    if aspect_ratio > 1.3 or aspect_ratio < 0.7:  # Far from square
                        raw_score *= 0.6
                
                scores[media_type] = min(raw_score, 100)  # Cap at 100%
        
        # Get the media type with highest confidence
        if scores:
            best_match = max(scores.items(), key=lambda x: x[1])
            return best_match
        
        return ('unknown', 0.0)
    
    def get_media_features(self, media_type: str) -> Optional[Dict[str, Any]]:
        """Get the feature configuration for a specific media type."""
        return self.media_types.get(media_type, {}).get('features')
    
    def add_media_type(self, 
                      name: str, 
                      aspect_ratio_range: Tuple[float, float],
                      features: Dict[str, Any]) -> None:
        """Add a new media type configuration."""
        self.media_types[name] = {
            'aspect_ratio_range': aspect_ratio_range,
            'features': features
        }
