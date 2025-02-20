"""
Media type definitions and base classes.
"""
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Dict, Any
import cv2
import numpy as np
import pytesseract
from src.vision.processor import extract_text_from_image, preprocess_image
from src.enrichment.api_client import search_movie_details

class MediaType(Enum):
    """Available media types."""
    VHS = auto()
    DVD = auto()
    CD = auto()
    VINYL = auto()
    CASSETTE = auto()

@dataclass
class MediaMetadata:
    """Common metadata for all media types."""
    title: Optional[str] = None
    year: Optional[int] = None
    condition: Optional[str] = None
    dimensions: Optional[tuple[int, int]] = None  # width, height in pixels
    notes: Optional[str] = None
    additional_info: Dict[str, Any] = None

class MediaProcessor:
    """Base class for media processing."""
    
    def __init__(self, media_type: MediaType):
        self.media_type = media_type
        self.image: Optional[np.ndarray] = None
        self.image_path: Optional[Path] = None
        self.metadata = MediaMetadata()
        
    def load_image(self, image_path: str | Path) -> bool:
        """Load image from path."""
        try:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {path}")
                
            image = cv2.imread(str(path))
            if image is None:
                raise ValueError(f"Failed to load image: {path}")
                
            self.image = image
            self.image_path = path
            self.metadata.dimensions = (image.shape[1], image.shape[0])
            return True
            
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
            
    def process(self) -> Dict[str, Any]:
        """Process the media and extract information."""
        raise NotImplementedError
        
    def get_preview_image(self) -> Optional[np.ndarray]:
        """Get a preview of the media image."""
        if self.image is None:
            return None
            
        # Convert to RGB for display
        return cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "media_type": self.media_type.name,
            "image_path": str(self.image_path) if self.image_path else None,
            "metadata": {
                "title": self.metadata.title,
                "year": self.metadata.year,
                "condition": self.metadata.condition,
                "dimensions": self.metadata.dimensions,
                "notes": self.metadata.notes,
                "additional_info": self.metadata.additional_info
            }
        }

class VHSProcessor(MediaProcessor):
    """VHS-specific processor."""
    
    def __init__(self):
        super().__init__(MediaType.VHS)
        
    def process(self) -> Dict[str, Any]:
        """Process VHS cover using existing pipeline."""
        if self.image is None:
            raise ValueError("No image loaded")
            
        try:
            # Preprocess image for OCR
            processed_img = preprocess_image(self.image)
            
            # Extract text using OCR
            extracted_text = extract_text_from_image(processed_img)
            
            # Search for movie details
            movie_details = search_movie_details(extracted_text)
            
            # Update metadata
            self.metadata.title = movie_details.get('title')
            self.metadata.year = movie_details.get('year')
            self.metadata.additional_info = {
                'extracted_text': extracted_text,
                'runtime': movie_details.get('runtime'),
                'genre': movie_details.get('genre'),
                'director': movie_details.get('director'),
                'cast': movie_details.get('cast'),
                'plot': movie_details.get('plot')
            }
            
            return self.to_dict()
            
        except Exception as e:
            raise Exception(f"VHS processing error: {str(e)}")

class DVDProcessor(MediaProcessor):
    """DVD-specific processor."""
    
    def __init__(self):
        super().__init__(MediaType.DVD)
        
    def process(self) -> Dict[str, Any]:
        if self.image is None:
            raise ValueError("No image loaded")
            
        try:
            # Use same image preprocessing as VHS but with DVD-specific enhancements
            processed_img = preprocess_image(self.image)
            
            # Extract text using OCR
            extracted_text = extract_text_from_image(processed_img)
            
            # Search for movie details - can reuse VHS movie lookup
            movie_details = search_movie_details(extracted_text)
            
            # DVD-specific metadata
            self.metadata.title = movie_details.get('title')
            self.metadata.year = movie_details.get('year')
            self.metadata.additional_info = {
                'extracted_text': extracted_text,
                'runtime': movie_details.get('runtime'),
                'genre': movie_details.get('genre'),
                'director': movie_details.get('director'),
                'cast': movie_details.get('cast'),
                'plot': movie_details.get('plot'),
                'dvd_features': self._extract_dvd_features(extracted_text),
                'region_code': self._detect_region_code(extracted_text)
            }
            
            return self.to_dict()
            
        except Exception as e:
            raise Exception(f"DVD processing error: {str(e)}")
            
    def _extract_dvd_features(self, text: str) -> list[str]:
        """Extract DVD special features from text."""
        features = []
        # Common DVD feature keywords
        keywords = [
            "commentary", "behind the scenes", "deleted scenes",
            "bonus", "feature", "interview", "trailer",
            "documentary", "making of", "extended"
        ]
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                features.append(keyword.title())
                
        return features
        
    def _detect_region_code(self, text: str) -> Optional[str]:
        """Try to detect DVD region code from text."""
        region_patterns = {
            "region 1": "1",
            "region 2": "2",
            "region 3": "3",
            "region 4": "4",
            "region free": "FREE",
            "all regions": "FREE"
        }
        
        text_lower = text.lower()
        for pattern, code in region_patterns.items():
            if pattern in text_lower:
                return code
        return None

class AudioMediaProcessor(MediaProcessor):
    """Base class for audio media (CD, Vinyl, Cassette)."""
    
    def __init__(self, media_type: MediaType):
        super().__init__(media_type)
        if media_type not in [MediaType.CD, MediaType.VINYL, MediaType.CASSETTE]:
            raise ValueError(f"Invalid audio media type: {media_type}")
    
    def _extract_audio_info(self, text: str) -> Dict[str, Any]:
        """Extract common audio media information."""
        info = {
            'artist': None,
            'album': None,
            'year': None,
            'tracks': [],
            'genre': None,
            'label': None
        }
        
        # Basic extraction based on common patterns
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            # Try to identify artist/album based on line position and length
            if i < 3 and len(line) > 0:  # Usually artist/album are at the top
                if not info['artist']:
                    info['artist'] = line
                elif not info['album']:
                    info['album'] = line
                    
            # Look for track listings
            if line and any(c.isdigit() for c in line[0:2]):
                info['tracks'].append(line)
                
            # Look for label information
            if '©' in line or '(c)' in line.lower():
                info['label'] = line
                
            # Try to extract year
            if not info['year']:
                for word in line.split():
                    if word.isdigit() and 1900 < int(word) < 2100:
                        info['year'] = int(word)
                        break
                        
        return info
            
    def process(self) -> Dict[str, Any]:
        if self.image is None:
            raise ValueError("No image loaded")
            
        try:
            # Process image
            processed_img = preprocess_image(self.image)
            extracted_text = extract_text_from_image(processed_img)
            
            # Extract audio information
            audio_info = self._extract_audio_info(extracted_text)
            
            # Update metadata
            self.metadata.title = audio_info['album']
            self.metadata.year = audio_info['year']
            self.metadata.additional_info = {
                'artist': audio_info['artist'],
                'tracks': audio_info['tracks'],
                'label': audio_info['label'],
                'extracted_text': extracted_text,
                'media_specific': self._get_media_specific_info(extracted_text)
            }
            
            return self.to_dict()
            
        except Exception as e:
            raise Exception(f"{self.media_type.name} processing error: {str(e)}")
            
    def _get_media_specific_info(self, text: str) -> Dict[str, Any]:
        """Get format-specific information. Override in subclasses."""
        return {}

class CDProcessor(AudioMediaProcessor):
    def __init__(self):
        super().__init__(MediaType.CD)
        
    def _get_media_specific_info(self, text: str) -> Dict[str, Any]:
        info = {}
        text_lower = text.lower()
        
        # CD-specific features
        if "enhanced cd" in text_lower:
            info['enhanced'] = True
        if "copy protected" in text_lower:
            info['copy_protected'] = True
        if "bonus track" in text_lower:
            info['has_bonus_tracks'] = True
            
        return info

class VinylProcessor(AudioMediaProcessor):
    def __init__(self):
        super().__init__(MediaType.VINYL)
        
    def _get_media_specific_info(self, text: str) -> Dict[str, Any]:
        info = {}
        text_lower = text.lower()
        
        # Vinyl-specific details
        speeds = ["33", "45", "78"]
        for speed in speeds:
            if f"{speed} rpm" in text_lower:
                info['speed'] = f"{speed} RPM"
                break
                
        sizes = ["7", "10", "12"]
        for size in sizes:
            if f"{size} inch" in text_lower or f"{size}\"" in text:
                info['size'] = f"{size} inch"
                break
                
        if "180" in text and "gram" in text_lower:
            info['weight'] = "180g"
            
        return info

class CassetteProcessor(AudioMediaProcessor):
    def __init__(self):
        super().__init__(MediaType.CASSETTE)
        
    def _get_media_specific_info(self, text: str) -> Dict[str, Any]:
        info = {}
        text_lower = text.lower()
        
        # Cassette-specific features
        if "dolby" in text_lower:
            info['dolby'] = True
        if "chrome" in text_lower:
            info['type'] = "Chrome"
        elif "metal" in text_lower:
            info['type'] = "Metal"
        else:
            info['type'] = "Normal"
            
        sides = ['a', 'b']
        info['tracks_by_side'] = {}
        current_side = None
        
        # Try to organize tracks by side
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if any(f"side {side}" in line_lower for side in sides):
                current_side = line_lower[0]  # Get 'a' or 'b'
                info['tracks_by_side'][current_side] = []
            elif current_side and line.strip():
                info['tracks_by_side'][current_side].append(line.strip())
                
        return info

def create_processor(media_type: str) -> MediaProcessor:
    """Factory function to create appropriate processor."""
    processors = {
        "VHS": VHSProcessor,
        "DVD": DVDProcessor,
        "CD": CDProcessor,
        "VINYL": VinylProcessor,
        "CASSETTE": CassetteProcessor
    }
    
    processor_class = processors.get(media_type.upper())
    if not processor_class:
        raise ValueError(f"Unknown media type: {media_type}")
        
    return processor_class()
