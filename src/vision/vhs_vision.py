"""
VHS vision processing module using LM Studio with optimized preprocessing.
"""
import base64
import io
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import cv2
import numpy as np
import requests
from PIL import Image

from .preprocessing import (
    PreprocessingPipeline,
    TextRegion,
    FastCLAHE,
    BilateralFilter,
    RegionDetector,
    ConfidenceScorer
)

logger = logging.getLogger(__name__)

class VHSVision:
    """Vision processing using LM Studio with optimized preprocessing."""
    
    def __init__(self, model: str = "local-model", save_debug: bool = False):
        """
        Initialize vision module.
        
        Args:
            model: Model ID to use
            save_debug: Whether to save debug images
        """
        self.save_debug = save_debug
        self.pipeline = PreprocessingPipeline()
        self.scorer = ConfidenceScorer()
        self._setup_lmstudio()
        
    def _setup_lmstudio(self):
        """Set up LM Studio connection and validate model."""
        try:
            response = requests.get("http://127.0.0.1:1234/v1/models", timeout=2)
            if response.status_code == 200:
                models_data = response.json()
                available_models = models_data.get('data', [])
                
                if available_models:
                    self.model = available_models[0]['id']
                    logger.info(f"Using detected model: {self.model}")
                else:
                    self.model = "local-model"
                    logger.info(f"No models detected, using default model: {self.model}")
            else:
                self.model = "local-model"
                logger.warning("Could not fetch models, using default model")
        except Exception as e:
            self.model = "local-model"
            logger.warning(f"Error checking models: {e}")
            
    def extract_info(self, image: Optional[np.ndarray], category: str) -> Dict[str, Any]:
        """
        Extract specific information from image with optimized preprocessing.
        
        Args:
            image: Image array or None
            category: Category to extract (title, year, runtime, studio, director, cast, rating)
            
        Returns:
            Dict containing extracted text, confidence and validation info
        """
        # Input validation
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            return {
                "text": "",
                "confidence": 0.0,
                "category": category,
                "validated": False,
                "error": "Invalid image input"
            }
            
        if not isinstance(category, str) or category not in {
            "title", "year", "runtime", "studio", "director", "cast", "rating"
        }:
            return {
                "text": "",
                "confidence": 0.0,
                "category": str(category),
                "validated": False,
                "error": "Invalid category"
            }
            
        # Save original image for debug
        if self.save_debug:
            try:
                self.save_debug_image(image, f"original_{category}")
            except Exception as e:
                logger.warning(f"Failed to save debug image: {e}")
        try:
            # Preprocess image and detect regions
            try:
                preprocessed, regions = self.pipeline.preprocess(image)
            except Exception as e:
                logger.error(f"Preprocessing failed: {e}")
                return {
                    "text": "",
                    "confidence": 0.0,
                    "category": category,
                    "validated": False,
                    "error": f"Preprocessing error: {str(e)}"
                }
            
            # Save preprocessed image for debug
            if self.save_debug:
                try:
                    self.save_debug_image(preprocessed, f"preprocessed_{category}")
                except Exception as e:
                    logger.warning(f"Failed to save debug image: {e}")
            
            # Define prompts for different categories
            prompts = {
                "title": "Extract movie title from VHS cover. ONLY return the title text, nothing else.",
                "year": "Extract release year from VHS cover. ONLY return the 4-digit year, nothing else.",
                "runtime": "Find the exact runtime shown on this VHS cover. Look for text showing how long the movie is (like '116 minutes' or '116 min'). Return ONLY the number. For example if you see '116 minutes', return just '116'.",
                "studio": "Extract studio/production company from VHS cover. ONLY return the studio name, nothing else.",
                "director": "Who directed this film? Look specifically for text that says exactly 'Directed by (name)'. Ignore producer credits. If you see 'A Steven Spielberg Production' but directed by someone else, return the actual director. Return ONLY the director's full name.",
                "cast": "Extract actor names from VHS cover. ONLY return comma-separated names, nothing else.",
                "rating": "Find the MPAA rating badge/logo on this VHS cover. It will be either G, PG, PG-13, R, or NC-17. Make sure to distinguish between similar looking ratings like PG and PG-13. Return ONLY the exact rating shown."
            }
            
            if category not in prompts:
                raise ValueError(f"Invalid category: {category}")
                
            # Process each region and find best match
            best_result = {
                "text": "",
                "confidence": 0.0,
                "category": category,
                "validated": False
            }
            
            if not regions:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "category": category,
                    "validated": False,
                    "error": "No text regions detected"
                }

            # Sort regions by size and process top 3
            for region in sorted(regions, key=lambda r: r.width * r.height, reverse=True)[:3]:
                if region.image is None or region.image.size == 0:
                    continue
                    
                try:
                    # Convert region image to base64
                    success, buffer = cv2.imencode('.jpg', region.image)
                    if not success:
                        logger.warning("Failed to encode region image")
                        continue
                    
                    image_base64 = base64.b64encode(buffer).decode('utf-8')
                except Exception as e:
                    logger.warning(f"Image encoding failed: {e}")
                    continue
                
                try:
                    # Make API request with timeouts and retries
                    for attempt in range(2):  # 1 retry
                        try:
                            response = requests.post(
                                "http://127.0.0.1:1234/v1/chat/completions",
                                json={
                                    "model": self.model,
                                    "messages": [
                                        {
                                            "role": "system",
                                            "content": "You are a VHS cover text extractor. Only return the exact text requested, nothing else. No explanations or complete sentences."
                                        },
                                        {
                                            "role": "user", 
                                            "content": [
                                                {"type": "text", "text": prompts[category]},
                                                {
                                                    "type": "image_url",
                                                    "image_url": {
                                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                                    }
                                                }
                                            ]
                                        }
                                    ],
                                    "temperature": 0.1,
                                    "max_tokens": 50
                                },
                                timeout=(5, 10)  # (connect timeout, read timeout)
                            )
                            response.raise_for_status()
                            break
                        except requests.exceptions.Timeout:
                            if attempt == 1:  # Last attempt
                                logger.warning(f"API timeout for region in category: {category}")
                                continue
                        except requests.exceptions.RequestException as e:
                            if attempt == 1:  # Last attempt
                                logger.error(f"API request failed: {e}")
                                continue
                            time.sleep(1)  # Brief delay before retry
                    
                    try:
                        result = response.json()
                        text = result["choices"][0]["message"]["content"].strip()
                        
                        # Basic validation before scoring
                        if not text or len(text) > 200:  # Arbitrary max length
                            continue
                            
                        confidence = self.scorer.score_text(text, category)
                        
                        # Update best result if confidence is higher
                        if confidence > best_result["confidence"]:
                            best_result = {
                                "text": text,
                                "confidence": confidence,
                                "category": category,
                                "validated": True
                            }
                            
                        # Early exit on high confidence
                        if confidence >= 90:
                            break
                            
                    except (KeyError, IndexError, ValueError) as e:
                        logger.warning(f"Failed to parse API response: {e}")
                        continue
                            
                except requests.exceptions.Timeout:
                    continue
                except Exception as e:
                    logger.error(f"API error processing region: {e}")
                    continue
                    
            if self.save_debug and best_result["validated"]:
                self.save_debug_image(
                    preprocessed,
                    f"success_{category}_{best_result['confidence']:.0f}"
                )
                
            return best_result
            
        except Exception as e:
            logger.error(f"Extraction error ({category}): {str(e)}")
            if self.save_debug:
                self.save_debug_image(image, f"error_{category}")
                
            return {
                "text": "",
                "confidence": 0.0,
                "category": category,
                "validated": False,
                            "error": str(e)
            }
            
    def save_debug_image(self, image: Optional[np.ndarray], name: str, debug_dir: str = "debug_output"):
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
