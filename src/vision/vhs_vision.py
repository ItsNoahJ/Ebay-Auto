"""
VHS vision processing module using LM Studio.
"""
import base64
import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import cv2
import numpy as np
import requests
from PIL import Image

logger = logging.getLogger(__name__)

class VHSVision:
    """Vision processing using LM Studio."""
    
    def __init__(self, model: str = "local-model", save_debug: bool = False):
        """
        Initialize vision module.
        
        Args:
            model: Model ID to use
            save_debug: Whether to save debug images
        """
        self.save_debug = save_debug
        
        # Get model info and validate
        try:
            response = requests.get("http://127.0.0.1:1234/v1/models", timeout=2)
            if response.status_code == 200:
                models_data = response.json()
                available_models = models_data.get('data', [])
                
                # Use first available model if any, otherwise use provided model
                if available_models:
                    self.model = available_models[0]['id']
                    logger.info(f"Using detected model: {self.model}")
                else:
                    self.model = model
                    logger.info(f"No models detected, using provided model: {self.model}")
            else:
                self.model = model
                logger.warning(f"Could not fetch models, using provided model: {self.model}")
        except Exception as e:
            self.model = model
            logger.warning(f"Error checking models, using provided model: {self.model}. Error: {e}")
            
    def extract_info(self, image: np.ndarray, info_type: str) -> Dict[str, Any]:
        """
        Extract specific information from image.
        
        Args:
            image: Image array
            info_type: Type of info to extract (title, year, runtime)
            
        Returns:
            Dict containing extracted text and confidence
        """
        try:
            # Convert image to base64
            success, buffer = cv2.imencode('.jpg', image)
            if not success:
                raise ValueError("Failed to encode image")
                
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Create vision request prompt based on info type
            if info_type == "title":
                prompt = "Extract the movie title from this VHS tape cover image. Return only the title text."
            elif info_type == "year":
                prompt = "Look for a release year in this VHS tape cover image. Return only the 4-digit year."
            elif info_type == "runtime":
                prompt = "Find the runtime duration in this VHS tape cover image. Return only the runtime in minutes (e.g. '120 min')."
            else:
                raise ValueError(f"Invalid info type: {info_type}")
            
            # Call LM Studio vision API
            response = requests.post(
                "http://127.0.0.1:1234/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "temperature": 0.1,  # Low temperature for consistent results
                    "max_tokens": 50  # Limit response length
                },
                timeout=30  # Longer timeout for image processing
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"API error: {response.text}")
                
            result = response.json()
            extracted_text = result["choices"][0]["message"]["content"].strip()
            
            # Calculate confidence (placeholder - could be improved)
            confidence = 90.0 if len(extracted_text) > 0 else 0.0
            
            return {
                "text": extracted_text,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Extraction error ({info_type}): {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e)
            }
            
    def save_debug_image(self, image: np.ndarray, name: str, debug_dir: str = "debug_output"):
        """Save debug image."""
        if self.save_debug:
            try:
                debug_path = Path(debug_dir)
                debug_path.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = debug_path / f"{name}_{timestamp}.jpg"
                
                cv2.imwrite(str(path), image)
                logger.debug(f"Saved debug image: {path}")
            except Exception as e:
                logger.error(f"Failed to save debug image: {e}")
