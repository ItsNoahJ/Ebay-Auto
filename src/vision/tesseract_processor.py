"""
Vision processing module for media image analysis.
"""
import os
import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional
import pytesseract
import os
from datetime import datetime
from src.models.media_detector import MediaDetector
from src.barcode.scanner import BarcodeScanner

class VisionProcessor:
    """
    Handles image processing and OCR for media images.
    """
    def __init__(self, debug_output_dir: str = "debug_output"):
        """Initialize the vision processor."""
        self.debug_output_dir = debug_output_dir
        os.makedirs(debug_output_dir, exist_ok=True)
        
        # Initialize components
        self.media_detector = MediaDetector()
        self.barcode_scanner = BarcodeScanner(debug_output_dir=debug_output_dir)
        
        # Lower confidence threshold for initial results
        self.confidence_threshold = 5
        
        # Configure Tesseract path
        if os.name == 'nt':  # Windows
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Optimized ROI regions for VHS tapes
        self.roi_regions = {
            "title": (0.05, 0.02, 0.95, 0.25),  # Wider region for title
            "year": (0.1, 0.3, 0.45, 0.45),     # Adjusted for typical VHS layout
            "runtime": (0.55, 0.3, 0.9, 0.45)    # Adjusted for typical VHS layout
        }
        
        # Enhanced Tesseract configurations for VHS text
        self.ocr_configs = {
            "title": "--psm 6 --oem 3",  # Assume uniform block of text
            "year": "--psm 7 -c tessedit_char_whitelist=0123456789",  # Assume single line, numbers only
            "runtime": "--psm 7 -c tessedit_char_whitelist=0123456789:" # Assume single line, numbers and colon
        }

    def _save_debug_image(self, img: np.ndarray, stage: str) -> str:
        """Save debug image with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{stage}_{timestamp}.jpg"
        path = os.path.join(self.debug_output_dir, filename)
        cv2.imwrite(path, img)
        return path

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Advanced contrast enhancement with multiple techniques."""
        # Convert to float32
        img_float = image.astype(np.float32) / 255.0
        
        # Apply CLAHE for local contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        clahe_1 = clahe.apply((img_float * 255).astype(np.uint8))
        
        # Gamma correction to boost mid-tones
        gamma = 1.5
        gamma_corrected = np.power(clahe_1 / 255.0, gamma)
        gamma_corrected = (gamma_corrected * 255).astype(np.uint8)
        
        # Second pass CLAHE with different parameters
        clahe_2 = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))
        clahe_result = clahe_2.apply(gamma_corrected)
        
        # Local contrast enhancement using unsharp masking
        blur = cv2.GaussianBlur(clahe_result, (0, 0), 3.0)
        unsharp_mask = cv2.addWeighted(clahe_result, 1.5, blur, -0.5, 0)
        
        # Normalize to ensure full dynamic range
        min_val = np.min(unsharp_mask)
        max_val = np.max(unsharp_mask)
        
        if max_val > min_val:
            normalized = np.clip(((unsharp_mask - min_val) * 255.0) / 
                               (max_val - min_val), 0, 255).astype(np.uint8)
        else:
            normalized = unsharp_mask
            
        return normalized

    def _find_character_regions(self, image: np.ndarray) -> np.ndarray:
        """Enhanced character region detection using multiple techniques."""
        # Create HSV version for color-based segmentation
        hsv = cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2HSV)
        
        # Extract value channel and enhance it
        v_channel = hsv[:,:,2]
        enhanced_v = self._enhance_contrast(v_channel)
        
        # Lighter denoising to preserve more detail
        denoised = cv2.fastNlMeansDenoising(enhanced_v, 
                                           h=7,
                                           templateWindowSize=5,
                                           searchWindowSize=15)
        
        # Multi-level thresholding
        thresh_methods = [
            lambda img: cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
            lambda img: cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            lambda img: cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, 11, 2)
        ]
        
        # Combine results from different thresholding methods
        binary_masks = []
        for thresh_method in thresh_methods:
            binary = thresh_method(denoised)
            binary_masks.append(binary)
        
        # Combine masks
        combined_mask = np.zeros_like(image)
        for mask in binary_masks:
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        return combined_mask

    def _preprocess_image(self, image: np.ndarray, media_type: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Enhanced preprocessing pipeline with media-specific handling."""
        # Get media-specific features
        media_features = self.media_detector.get_media_features(media_type)
        if media_features:
            self.roi_regions = dict(zip(
                ["title", "year", "runtime"],
                media_features['text_regions']
            ))
        
        debug_info = {}
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        debug_info['grayscale'] = self._save_debug_image(gray, "grayscale")
        
        # Enhance contrast
        enhanced = self._enhance_contrast(gray)
        debug_info['enhanced'] = self._save_debug_image(enhanced, "enhanced")
        
        # Find character regions
        char_regions = self._find_character_regions(enhanced)
        debug_info['char_regions'] = self._save_debug_image(char_regions, "char_regions")
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(char_regions, h=10)
        debug_info['denoised'] = self._save_debug_image(denoised, "denoised")
        
        return denoised, debug_info

    def _extract_roi_text(self, image: np.ndarray, region: Tuple[float, float, float, float], region_name: str) -> Tuple[str, float]:
        """Extract text from ROI with improved processing."""
        # Extract ROI
        height, width = image.shape[:2]
        x1 = int(width * region[0])
        y1 = int(height * region[1])
        x2 = int(width * region[2])
        y2 = int(height * region[3])
        roi = image[y1:y2, x1:x2]
        
        # Add padding
        pad = 20
        roi = cv2.copyMakeBorder(roi, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
        
        self._save_debug_image(roi, f"roi_{region_name}")
        
        # Multiple preprocessing attempts
        results = []
        
        # Original
        results.append(self._ocr_with_config(roi, self.ocr_configs[region_name]))
        
        # Inverted
        inverted = cv2.bitwise_not(roi)
        results.append(self._ocr_with_config(inverted, self.ocr_configs[region_name]))
        
        # Dilated
        kernel = np.ones((2,2), np.uint8)
        dilated = cv2.dilate(roi, kernel, iterations=2)
        results.append(self._ocr_with_config(dilated, self.ocr_configs[region_name]))
        
        # Eroded
        eroded = cv2.erode(roi, kernel, iterations=1)
        results.append(self._ocr_with_config(eroded, self.ocr_configs[region_name]))
        
        # Filter and select best result
        valid_results = [(text, conf) for text, conf in results if text and conf > 0]
        if not valid_results:
            return "", 0.0
        
        return max(valid_results, key=lambda x: (x[1], len(x[0])))

    def _ocr_with_config(self, image: np.ndarray, config: str) -> Tuple[str, float]:
        """Perform OCR with enhanced preprocessing and result processing."""
        try:
            # Scale up image to improve OCR
            height, width = image.shape[:2]
            scale = max(1, int(1000 / min(width, height)))
            if scale > 1:
                image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

            # Bilateral filter to reduce noise while preserving edges
            image = cv2.bilateralFilter(image, 9, 75, 75)
            
            # Ensure black text on white background
            if np.mean(image) < 127:
                image = cv2.bitwise_not(image)

            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=config)
            
            text_parts = []
            conf_sum = 0
            conf_count = 0
            
            for i, conf in enumerate(data["conf"]):
                if conf > 0:
                    text = data["text"][i].strip()
                    if text:
                        # Additional text cleaning based on field
                        if "tessedit_char_whitelist=0123456789" in config:
                            text = ''.join(c for c in text if c.isdigit())
                        text_parts.append(text)
                        conf_sum += conf
                        conf_count += 1
            
            if conf_count == 0:
                return "", 0.0
            
            text = " ".join(text_parts)
            text = " ".join(text.split())  # Normalize whitespace
            
            # Calculate weighted confidence score
            confidence = (conf_sum / conf_count) * min(1, len(text) / 3)  # Reduce confidence for very short results
            
            return text, confidence
            
        except Exception as e:
            print(f"OCR error: {e}")
            return "", 0.0

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """Process media image with comprehensive pipeline."""
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Save original for debug
        orig_debug_path = self._save_debug_image(image, "original")
        
        # Detect media type
        media_type, type_confidence = self.media_detector.detect_media_type(image)
        
        # Scan for barcodes
        barcode_results = self.barcode_scanner.scan_image(image)
        
        # Preprocess image with media-specific handling
        processed, debug_paths = self._preprocess_image(image, media_type)
        proc_debug_path = self._save_debug_image(processed, "preprocessed")
        
        # Extract text from regions
        results = {}
        debug_info = {
            "original_image": orig_debug_path,
            "processed_image": proc_debug_path,
            "debug_images": debug_paths,
            "confidence_scores": {},
            "media_type": {
                "detected": media_type,
                "confidence": type_confidence
            },
            "barcode_info": barcode_results["debug_info"]
        }
        
        for region_name, coords in self.roi_regions.items():
            text, confidence = self._extract_roi_text(processed, coords, region_name)
            results[region_name] = text
            debug_info["confidence_scores"][region_name] = confidence
        
        # Add barcode data if found
        if barcode_results["barcodes"]:
            results["barcode"] = barcode_results["barcodes"][0]["data"]
            if "metadata" in barcode_results["barcodes"][0]:
                results["barcode_metadata"] = barcode_results["barcodes"][0]["metadata"]
        
        return {
            "extracted_data": results,
            "debug_info": debug_info
        }

    def validate_results(self, results: Dict[str, Any]) -> bool:
        """Validate results with confidence threshold."""
        confidence_scores = results["debug_info"]["confidence_scores"]
        return all(score >= self.confidence_threshold for score in confidence_scores.values())
