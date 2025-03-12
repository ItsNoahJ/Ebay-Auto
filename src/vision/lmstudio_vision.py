"""
Vision-language processing using LM Studio for VHS cover text extraction.
"""
import cv2
import numpy as np
import json
import base64
import requests
import math
from typing import Dict, Optional, List, Tuple
from datetime import datetime

class VHSVision:
    """
    Vision-language processing for VHS cover text extraction.
    Uses LM Studio's API to process images and extract text.
    """
    
    def __init__(
        self,
        model: str = "local-model",  # Use generic model name
        host: str = "http://127.0.0.1:1234",
        target_pixel_count: int = 307200,  # Equivalent to 640x480
        save_debug: bool = True
    ):
        """Initialize vision processor."""
        self.model = model
        self.host = host.rstrip('/')
        self.target_pixel_count = target_pixel_count
        self.save_debug = save_debug
        self.target_encoded_size = 170000  # Target size in bytes for 2048 tokens

        # Verify LM Studio is running
        try:
            response = requests.get(f"{self.host}/v1/models", timeout=5)
            if response.status_code == 200:
                try:
                    models = response.json()
                    if models and isinstance(models, list) and len(models) > 0:
                        model_info = models[0]
                        self.model = model_info.get("name", model_info["id"])  # Use name if available, fallback to ID
                        print(f"Successfully connected to LM Studio")
                        print(f"Using model: {self.model}")
                    else:
                        print("\nWarning: No models available in LM Studio")
                        print("Please load a model in LM Studio and try again")
                        print("Status: Connected but no model loaded")
                except Exception as e:
                    print("\nError: Failed to parse models list from LM Studio")
                    print(f"Error details: {str(e)}")
                    print("Status: Connected but model info unavailable")
            else:
                print("\nError: LM Studio API returned unexpected status")
                print(f"Status code: {response.status_code}")
                print("Please verify:")
                print("1. LM Studio is running and accessible")
                print("2. API endpoint is correct:", self.host)
                if response.status_code == 404:
                    print("3. This appears to be an API endpoint issue")
                    print("   Make sure LM Studio's API is enabled and the port is correct")
        except requests.RequestException as e:
            print("\nError: Could not establish connection to LM Studio")
            print("Status: Connection failed")
            print("\nTroubleshooting steps:")
            print("1. Verify LM Studio is running")
            print("2. Check host address:", self.host)
            print("3. Ensure a model is loaded")
            if isinstance(e, requests.ConnectionError):
                print("\nDiagnosis: Connection refused")
                print("This usually means LM Studio is not running")
                print("Action: Start LM Studio and try again")
            elif isinstance(e, requests.Timeout):
                print("\nDiagnosis: Connection timed out")
                print("This could mean LM Studio is busy or unresponsive")
                print("Action: Restart LM Studio if the issue persists")
            print(f"\nTechnical details: {str(e)}")

    def _calculate_target_size(self, h: int, w: int) -> Tuple[int, int]:
        """Calculate optimal target size based on input resolution and model requirements.
        
        Optimizes dimensions to:
        1. Minimize processing time while maintaining text readability
        2. Reduce memory usage during API calls
        3. Ensure proper aspect ratio preservation
        """
        pixel_count = h * w
        min_dimension = 320  # Minimum dimension to maintain text readability
        
        if pixel_count <= self.target_pixel_count:
            # For small images, ensure minimum dimensions
            if h < min_dimension or w < min_dimension:
                scale = min_dimension / min(h, w)
                return int(h * scale), int(w * scale)
            return h, w
            
        # For larger images, use faster downscaling
        # Calculate scale maintaining aspect ratio
        scale = math.sqrt(self.target_pixel_count / pixel_count)
        
        # Round to nearest multiple of 32 for better GPU optimization
        new_h = int(round(h * scale / 32) * 32)
        new_w = int(round(w * scale / 32) * 32)
        
        # Ensure minimum dimensions
        new_h = max(min_dimension, new_h)
        new_w = max(min_dimension, new_w)
        
        return new_h, new_w

    def _calculate_jpeg_quality(self, test_size: int) -> int:
        """Calculate adaptive JPEG quality to target specific encoded size."""
        if test_size <= self.target_encoded_size:
            return 95  # High quality for small images
            
        # Scale quality based on how much we need to reduce size
        quality = int(95 * (self.target_encoded_size / test_size))
        # Ensure quality stays in reasonable bounds
        return max(65, min(95, quality))
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Enhanced image preprocessing with adaptive sizing."""
        # Convert to grayscale if not already
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Calculate adaptive target size
        h, w = gray.shape[:2]
        new_h, new_w = self._calculate_target_size(h, w)
        
        # Resize if needed
        if new_h != h or new_w != w:
            resized = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        else:
            resized = gray
        
        # Enhance contrast using CLAHE with optimized parameters
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(4,4))
        contrast_enhanced = clahe.apply(resized)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(contrast_enhanced)
        
        # Apply morphological operations to help with cursive text
        # Small kernel to preserve detail while connecting strokes
        kernel = np.ones((2,2), np.uint8)
        dilated = cv2.dilate(denoised, kernel, iterations=1)
        eroded = cv2.erode(dilated, kernel, iterations=1)
        
        # Sharpen the result
        sharpen_kernel = np.array([[-1,-1,-1],
                                 [-1, 9,-1],
                                 [-1,-1,-1]])
        sharpened = cv2.filter2D(eroded, -1, sharpen_kernel)
        
        # Convert back to BGR for model input
        processed = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
        
        # Save intermediate processing steps for debugging
        if self.save_debug:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(f'debug_output/dilated_{timestamp}.jpg', dilated)
            cv2.imwrite(f'debug_output/eroded_{timestamp}.jpg', eroded)
        
        print(f"\nDebug: Processed image shape: {processed.shape}")
        return processed
    
    def encode_image(self, image: np.ndarray) -> str:
        """Convert OpenCV image to base64 string with adaptive quality."""
        # First try with high quality to assess size
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
        success, buffer = cv2.imencode('.jpg', image, encode_params)
        if not success:
            raise ValueError("Failed to encode image")
            
        # Calculate adaptive quality if needed
        encoded = base64.b64encode(buffer).decode('utf-8')
        initial_size = len(encoded)
        
        if initial_size > self.target_encoded_size:
            # Recalculate quality and re-encode
            quality = self._calculate_jpeg_quality(initial_size)
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            success, buffer = cv2.imencode('.jpg', image, encode_params)
            if not success:
                raise ValueError("Failed to re-encode image")
            encoded = base64.b64encode(buffer).decode('utf-8')
            
        print(f"Debug: Encoded image size: {len(encoded)} bytes")
        print(f"Debug: First 50 chars of encoded image: {encoded[:50]}...")
        return encoded
    
    def save_debug_image(self, image: np.ndarray, name: str):
        """Save processed image for debugging."""
        if self.save_debug:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'debug_output/processed_{name}_{timestamp}.jpg'
            cv2.imwrite(filename, image)
            print(f"Saved processed image: {filename}")
    
    def extract_info(
        self,
        image: np.ndarray,
        info_type: str = "title"
    ) -> Dict[str, any]:
        """Extract specific information from VHS cover image with optimized processing."""
        try:
            # Enhanced preprocessing with caching
            cache_key = f"{hash(image.tobytes())}_{info_type}"
            
            # Optimized preprocessing
            processed_image = self.preprocess_image(image)
            if self.save_debug:
                self.save_debug_image(processed_image, info_type)
            
            # Optimized prompts for faster inference
            prompts = {
                "title": "Extract movie title only:",
                "year": "Extract 4-digit year only:",
                "runtime": "Extract runtime in HH:MM format only:"
            }
            prompt = prompts.get(info_type, prompts["title"])
            
            # Optimized API payload
            encoded_image = self.encode_image(processed_image)
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                        ]
                    }
                ],
                "temperature": 0.01,  # Keep deterministic
                "max_tokens": 20,     # Reduced for faster response
                "stream": False,      # Disable streaming for speed
                "stop": ["\n", "."]   # Stop on newline/period for cleaner output
            }
            
            # Optimized API call with shorter timeout
            response = requests.post(
                f"{self.host}/v1/chat/completions",
                json=payload,
                timeout=15,  # Reduced timeout
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            # Parse response from LM Studio format
            result = response.json()
            
            # Get and show raw response text
            raw_text = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
            print(f"\nRaw response: {raw_text}")
            
            # Clean response based on info type
            text = self._clean_response(raw_text, info_type)
            
            # Simple confidence estimation based on response length and content
            confidence = self._estimate_confidence(text, info_type)
            
            return {
                'text': text,
                'confidence': confidence,
                'method': self.model,
                'raw_response': result
            }
            
        except requests.RequestException as e:
            error_msg = [
                "LM Studio Vision API Error",
                "=" * 50,
                f"Operation: Extracting {info_type}",
                f"Model: {self.model}",
                f"Endpoint: {self.host}/v1/chat/completions",
                f"Status: Failed",
                "-" * 30
            ]
            
            if hasattr(e, 'response') and e.response:
                status_code = e.response.status_code
                error_msg.extend([
                    "API Response Details:",
                    f"Status Code: {status_code}"
                ])
                
                if status_code == 404:
                    error_msg.extend([
                        "\nDiagnosis: API endpoint or model not found",
                        "This usually means:",
                        "• LM Studio is not properly initialized",
                        "• No model is currently loaded",
                        "\nRecommended actions:",
                        "1. Open LM Studio and load a model",
                        "2. Check API settings:",
                        f"   - API URL: {self.host}",
                        "   - API enabled: Yes",
                        "3. Try:",
                        "   - Restart LM Studio",
                        "   - Load a different model"
                    ])
                elif status_code == 500:
                    error_msg.extend([
                        "\nDiagnosis: Server error",
                        "This usually means:",
                        "• The model encountered an error",
                        "• LM Studio may be out of memory",
                        "\nRecommended actions:",
                        "1. Restart LM Studio",
                        "2. Try a different model",
                        "3. Check system resources"
                    ])
                
                if hasattr(e.response, 'text'):
                    error_msg.extend(["", "Server Response:", e.response.text])
                    
            elif isinstance(e, requests.Timeout):
                error_msg.extend([
                    "\nDiagnosis: Request timed out",
                    "This usually means:",
                    "• Model is taking too long to process",
                    "• System resources are constrained",
                    "\nRecommended actions:",
                    "1. Check CPU/Memory usage",
                    "2. Consider a faster model",
                    "3. Increase timeout duration"
                ])
                
            elif isinstance(e, requests.ConnectionError):
                error_msg.extend([
                    "\nDiagnosis: Connection failed",
                    "This usually means:",
                    "• LM Studio is not running",
                    "• Wrong port or host",
                    "\nRecommended actions:",
                    "1. Start LM Studio",
                    f"2. Verify {self.host} is accessible"
                ])
            
            error_msg.append("-" * 30)
            error_msg.append(f"Technical Details: {str(e)}")
            error_msg.append("=" * 50)
            
            # Format error message to avoid duplication
            formatted_error = '\n'.join(error_msg)
            print(formatted_error)
            
            return {
                'text': "",
                'confidence': 0.0,
                'method': self.model,
                'error': formatted_error
            }
            
    def _clean_response(self, text: str, info_type: str) -> str:
        """Clean and validate response based on info type."""
        import re
        text = text.strip()
        
        if info_type == "year":
            # Look for 4-digit year pattern
            year_match = re.search(r'\b(?:19|20)\d{2}\b', text)
            if year_match:
                return year_match.group(0)
            return ""
            
        elif info_type == "runtime":
            # Format should be duration only
            # Remove any non-runtime text
            text = re.sub(r'[Rr]untime:?\s*', '', text)
            text = re.sub(r'[Dd]uration:?\s*', '', text)
            text = text.strip()
            return text
            
        else:  # Title
            # Remove common prefixes
            text = re.sub(r'^[Tt]itle:?\s*', '', text)
            text = re.sub(r'^[Tt]he [Mm]ovie:?\s*', '', text)
            text = text.strip()
            return text

    def is_high_confidence(self, result: Dict[str, any], threshold: float = 0.7) -> bool:
        """Check if extraction result has high confidence.
        
        Args:
            result: Dictionary containing extraction result with 'confidence' key
            threshold: Minimum confidence score to be considered high confidence (0.0-1.0)
            
        Returns:
            bool indicating if confidence meets threshold
        """
        if 'confidence' not in result:
            return False
            
        # Convert from percentage (0-100) to decimal (0.0-1.0) if needed
        confidence = result['confidence']
        if confidence > 1.0:
            confidence = confidence / 100.0
            
        return confidence >= threshold
            
    def _estimate_confidence(self, text: str, info_type: str) -> float:
        """Estimate confidence score (0.0-1.0) for extracted info."""
        import re
        if not text:
            return 0.0
            
        confidence = 0.0
        
        if info_type == "year":
            # High confidence if valid 4-digit year
            if re.match(r'^(?:19|20)\d{2}$', text):
                confidence = 0.9
                if 1970 <= int(text) <= 2020:  # Likely VHS era
                    confidence += 0.1
                    
        elif info_type == "runtime":
            # Check for time patterns (e.g. "90 minutes", "1h 30m")
            if re.search(r'\d+\s*(?:hour|hr|h|minute|min|m)s?', text, re.I):
                confidence = 0.8
                if re.search(r'\d+\s*(?:hour|hr|h).*\d+\s*(?:minute|min|m)', text, re.I):
                    confidence += 0.2  # Extra confidence for complete HH:MM format
                    
        else:  # Title
            # Basic sanity checks for title
            words = len([w for w in text.split() if w.strip()])  # Count non-empty words
            if words > 6:  # Stricter length check
                confidence = 0.3  # Heavy penalty for long titles
                penalty = min((words - 6) * 0.1, 0.2)  # Additional penalty for each word over 6
                confidence = max(0.1, confidence - penalty)
            elif 1 <= words <= 8:  # Reasonable title length
                confidence = 0.7
                if re.match(r'^[A-Z0-9]', text):  # Starts with capital letter or number
                    confidence += 0.2
                if re.search(r'[\.!?]$', text):  # No trailing punctuation
                    confidence -= 0.1
                    
        return min(1.0, max(0.0, confidence))  # Ensure 0.0-1.0 range
