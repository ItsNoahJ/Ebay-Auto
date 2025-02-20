"""
Barcode detection and scanning module.
"""
import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from pyzbar import pyzbar
import requests
from datetime import datetime

class BarcodeScanner:
    """Handles barcode detection and information lookup."""
    
    def __init__(self, debug_output_dir: str = "debug_output"):
        """Initialize the barcode scanner."""
        self.debug_output_dir = debug_output_dir
        self.last_scan_time = datetime.min
        self.min_scan_interval = 1.0  # Minimum seconds between API calls
        
    def _save_debug_image(self, img: np.ndarray, stage: str) -> str:
        """Save debug image with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"barcode_{stage}_{timestamp}.jpg"
        path = f"{self.debug_output_dir}/{filename}"
        cv2.imwrite(path, img)
        return path

    def _enhance_barcode_region(self, image: np.ndarray) -> np.ndarray:
        """Enhance image for better barcode detection."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, h=10)
        
        return denoised

    def _detect_barcode_regions(self, image: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Detect potential barcode regions in the image.
        Returns list of (region_image, (x, y, w, h)).
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Edge detection
        edges = cv2.Canny(gray, 50, 200)
        
        # Dilate to connect edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(
            dilated,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter and process potential barcode regions
        regions = []
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio and size
            aspect_ratio = w / float(h)
            if 2.0 < aspect_ratio < 5.0 and w > 100:
                # Extract region with padding
                pad = 20
                x1 = max(0, x - pad)
                y1 = max(0, y - pad)
                x2 = min(image.shape[1], x + w + pad)
                y2 = min(image.shape[0], y + h + pad)
                
                region = image[y1:y2, x1:x2]
                regions.append((region, (x1, y1, x2-x1, y2-y1)))
        
        return regions

    def scan_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Scan image for barcodes.
        
        Args:
            image: OpenCV image array
            
        Returns:
            Dictionary with scan results and debug info
        """
        debug_info = {
            "detected_regions": [],
            "processing_steps": []
        }
        
        # Save original
        debug_info["original"] = self._save_debug_image(image, "original")
        
        # Detect barcode regions
        regions = self._detect_barcode_regions(image)
        
        results = []
        for i, (region, bbox) in enumerate(regions):
            # Save region debug image
            region_path = self._save_debug_image(region, f"region_{i}")
            debug_info["detected_regions"].append({
                "bbox": bbox,
                "image": region_path
            })
            
            # Enhance region
            enhanced = self._enhance_barcode_region(region)
            debug_info["processing_steps"].append(
                self._save_debug_image(enhanced, f"enhanced_region_{i}")
            )
            
            # Scan for barcodes
            barcodes = pyzbar.decode(enhanced)
            
            for barcode in barcodes:
                result = {
                    "type": barcode.type,
                    "data": barcode.data.decode("utf-8"),
                    "bbox": bbox,
                    "confidence": None  # pyzbar doesn't provide confidence scores
                }
                
                # Get additional info from online database
                if barcode.type in ['EAN13', 'UPC-A']:
                    metadata = self._lookup_barcode(barcode.data.decode("utf-8"))
                    if metadata:
                        result["metadata"] = metadata
                
                results.append(result)
        
        return {
            "barcodes": results,
            "debug_info": debug_info
        }

    def _lookup_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """
        Look up barcode information from online database.
        Rate limited to prevent API abuse.
        """
        # Check rate limit
        now = datetime.now()
        if (now - self.last_scan_time).total_seconds() < self.min_scan_interval:
            return None
            
        self.last_scan_time = now
        
        # UPC database API (example)
        try:
            response = requests.get(
                f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    item = data['items'][0]
                    return {
                        "title": item.get("title"),
                        "brand": item.get("brand"),
                        "category": item.get("category"),
                        "description": item.get("description"),
                        "source": "upcitemdb"
                    }
            
        except Exception as e:
            print(f"Barcode lookup error: {e}")
            
        return None
