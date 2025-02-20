"""
Vision-language processing using LM Studio for VHS cover text extraction.
"""
import cv2
import numpy as np
import json
import base64
import requests
from typing import Dict, Optional, List, Tuple
from datetime import datetime

class VHSVision:
    """
    Vision-language processing for VHS cover text extraction.
    Uses LM Studio's API to process images and extract text.
    """
    
    def __init__(
        self,
        model: str = "lmstudio-community/minicpm-o-2_6",
        host: str = "http://127.0.0.1:1234",
        target_size: int = 768,
        save_debug: bool = True
    ):
        # Verify LM Studio is running
        try:
            response = requests.get(f"{host.rstrip('/')}/v1/models", timeout=5)
            response.raise_for_status()
            print("Successfully connected to LM Studio")
        except requests.RequestException as e:
            print("\nError: Could not connect to LM Studio")
            print("1. Make sure LM Studio is running")
            print("2. Verify the host address is correct")
            print("3. Check if the model is loaded")
            print(f"\nDetailed error: {str(e)}")
        """
        Initialize vision processor.
        
        Args:
            model: Name of vision-language model
            host: Ollama API host address
            target_size: Target size for image resizing (preserves aspect ratio)
            save_debug: Whether to save debug images
        """
        self.model = model
        self.host = host.rstrip('/')
        self.target_size = target_size
        self.save_debug = save_debug
    
    def resize_image(self, image: np.ndarray) -> np.ndarray:
        """Resize image while preserving aspect ratio."""
        h, w = image.shape[:2]
        if h > w:
            new_h = self.target_size
            new_w = int(w * (self.target_size / h))
        else:
            new_w = self.target_size
            new_h = int(h * (self.target_size / w))
        
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        print(f"\nDebug: Resized image shape: {resized.shape}")
        return resized
    
    def encode_image(self, image: np.ndarray) -> str:
        """Convert OpenCV image to base64 string."""
        success, buffer = cv2.imencode('.jpg', image)
        if not success:
            raise ValueError("Failed to encode image")
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
        """
        Extract specific information from VHS cover image.
        
        Args:
            image: Original image
            info_type: Type of information to extract ("title", "year", "runtime")
            
        Returns:
            dict containing extracted info, confidence score, and method used
        """
        # Resize image for better processing
        processed_image = self.resize_image(image)
        self.save_debug_image(processed_image, info_type)
        
        # Natural language prompts for each info type
        if info_type == "title":
            system = "You are an OCR system. Your task is to literally read and transcribe the largest text that appears to be a movie title on this VHS cover. Do not use any external knowledge about movies - only read what is actually printed."
            prompt = "What text appears to be the movie title on this VHS cover? Return ONLY the text as it appears, with no interpretation or assumptions. If you cannot read the text clearly, say 'Unable to read text clearly'."
        elif info_type == "year":
            system = "You are an OCR system. Your task is to find and read ONLY clearly visible 4-digit numbers that are definitely printed on THIS VHS cover - ignore any other objects, books, or items in the image. Only report numbers from the VHS cover itself."
            prompt = "Look ONLY at the VHS cover (not books or other items) for any clearly visible 4-digit numbers. If you see a number ON THE VHS COVER ITSELF with 100% certainty, return ONLY that number. Otherwise say 'No year visible'. Only report text from the VHS cover."
        elif info_type == "runtime":
            system = "You are an OCR system. Your task is to find ONLY runtime text that appears directly on THIS VHS cover - ignore any other objects or sources. Look for numbers followed by units like 'min', 'mins', 'minutes', 'hr', 'hour'. Only report what is clearly printed on the VHS cover itself."
            prompt = "Look ONLY at the VHS cover for any runtime text (numbers with time units). If you see a runtime ON THE VHS COVER ITSELF with 100% certainty, return ONLY that runtime. Otherwise say 'No runtime visible'. Be extremely conservative - only report text from the VHS cover."
            
        # Build the complete prompt
        full_prompt = f"{system}\n\n{prompt}"
        
        # Prepare request matching LM Studio's vision API format
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{self.encode_image(image)}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 50,
            "stream": False,
            "temperature": 0.01  # Make model extremely conservative
        }
        
        try:
            # Send request to Ollama
            response = requests.post(
                f"{self.host}/v1/chat/completions",
                json=payload,
                timeout=30
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
            error_msg = []
            error_msg.append("LM Studio API error:")
            error_msg.append(str(e))
            
            if isinstance(e, requests.Timeout):
                error_msg.append("\nRequest timed out. Possible causes:")
                error_msg.append("1. LM Studio is busy processing")
                error_msg.append("2. Image size might be too large")
                error_msg.append("3. Model might be too slow")
            elif isinstance(e, requests.ConnectionError):
                error_msg.append("\nConnection failed. Please verify:")
                error_msg.append("1. LM Studio is running")
                error_msg.append("2. The host address is correct")
                error_msg.append("3. No firewall is blocking the connection")
            
            if hasattr(e, 'response') and e.response:
                if e.response.status_code == 404:
                    error_msg.append("\nAPI endpoint not found:")
                    error_msg.append("1. Check if model is loaded in LM Studio")
                    error_msg.append("2. Verify API endpoint is correct")
                if hasattr(e.response, 'text'):
                    error_msg.append(f"\nServer response: {e.response.text}")
            
            print('\n'.join(error_msg))
            return {
                'text': "",
                'confidence': 0.0,
                'method': self.model,
                'error': '\n'.join(error_msg)
            }
    
    def _clean_response(self, text: str, info_type: str) -> str:
        """Clean model response based on info type."""
        # Handle special responses
        if any(phrase in text.lower() for phrase in [
            'unable to read', 'cannot read', 'not visible', 'no runtime',
            'no year', "can't read", 'not clear', 'no title'
        ]):
            return ''
        
        # Remove any explanatory text after newlines
        text = text.split('\n')[0].strip()
        
        if info_type == "title":
            # Remove any qualifying statements
            text = text.split(', which')[0].strip()
            text = text.split(' - ')[0].strip()
            text = text.split(' (')[0].strip()
        
        elif info_type == "runtime":
            # Extract just the numbers and "min"
            import re
            match = re.search(r'(\d+)\s*min', text.lower())
            if match:
                text = f"{match.group(1)} min"
                
        elif info_type == "year":
            # Extract first 4-digit number
            import re
            match = re.search(r'\b(19|20)\d{2}\b', text)
            if match:
                text = match.group(0)
                
        return text
    
    def _estimate_confidence(self, text: str, info_type: str) -> float:
        """
        Estimate confidence score based on response characteristics and text validity.
        
        Uses stricter heuristics to validate the extracted text matches expected patterns
        for titles, years, and runtimes.
        """
        if not text or text.strip() == '':
            return 0.0
            
        # Start with low base confidence
        confidence = 30.0
        
        # Check for garbled text indicators
        if '<' in text or '>' in text or '|' in text or '‽' in text:
            return 0.0
            
        if info_type == "year":
            # Must be exactly 4 digits between 1900-2025
            # Less restrictive year validation - allow sci-fi years
            if text.isdigit() and len(text) == 4:
                year = int(text)
                if 1900 <= year <= 2100:  # Allow future years
                    confidence += 50.0
                    if 1950 <= year <= 2025:  # Higher confidence for typical VHS era
                        confidence += 20.0
                
        elif info_type == "runtime":
            # Must contain digits followed by "min"
            import re
            if re.search(r'^\d+\s*min', text.lower()):
                confidence += 70.0
                
        elif info_type == "title":
            # Title validation:
            # - Must contain mostly ASCII letters
            # - Should have reasonable length
            # - Should not have unusual character patterns
            # Calculate ratio of valid title characters (letters, common punctuation)
            valid_chars = lambda c: c.isascii() and (c.isalpha() or c in ' :!-.')
            valid_ratio = sum(valid_chars(c) for c in text) / len(text) if text else 0
            
            if (len(text) >= 2 and len(text) <= 100 and  # Reasonable length
                valid_ratio > 0.8 and                     # Mostly valid characters
                ' ' in text and                          # Contains spaces
                not any(c.isdigit() for c in text)):     # No digits in title
                confidence += 70.0
        
        return min(max(confidence, 0.0), 100.0)
    
    def is_high_confidence(
        self,
        result: Dict[str, any],
        threshold: float = 70.0
    ) -> bool:
        """Check if OCR result meets confidence threshold."""
        return result['confidence'] >= threshold
