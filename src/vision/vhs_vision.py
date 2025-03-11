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
from typing import Dict, Any, Optional, List, Tuple

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
    ConfidenceScorer,
    TimeoutError
)

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors."""
    pass

class VHSVision:
    """Vision processing using LM Studio with optimized preprocessing."""
    
    # Class-level configuration
    MAX_RETRIES = 3
    INITIAL_TIMEOUT = (10, 30)  # (connect timeout, read timeout)
    MAX_BACKOFF = 15  # Maximum backoff time in seconds
    API_BASE_URL = "http://127.0.0.1:1234"
    
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
        self.model = model
        self.preprocessing_images = {}
        self._setup_lmstudio()
        
    def _setup_lmstudio(self):
        """Set up LM Studio connection and validate model."""
        try:
            # Try to get available models with longer timeout
            models = self._make_api_request("GET", "/v1/models", timeout=(5, 15), max_retries=2)
            available_models = models.get('data', [])
            
            if available_models:
                self.model = available_models[0]['id']
                logger.info(f"Using detected model: {self.model}")
                
                # Test model with a simple query
                logger.info("Testing model...")
                try:
                    test_result = self._make_api_request(
                        "POST",
                        "/v1/chat/completions",
                        json_data={
                            "model": self.model,
                            "messages": [
                                {"role": "user", "content": "Test connection"}
                            ],
                            "max_tokens": 5
                        },
                        timeout=(5, 15)
                    )
                    logger.info("Model test successful")
                except Exception as e:
                    logger.warning(f"Model test failed: {str(e)}")
            else:
                logger.warning(f"No models detected, using default model: {self.model}")
                
        except (APIError, TimeoutError) as e:
            logger.warning(f"Error checking models - LM Studio may need more time to initialize: {e}")
            # Keep default model
    
    def _make_api_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict] = None,
        timeout: Optional[Tuple[float, float]] = None,
        max_retries: Optional[int] = None
    ) -> Dict:
        """
        Make API request with retries and exponential backoff.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            json_data: Optional JSON payload
            timeout: Optional timeout tuple (connect, read)
            max_retries: Optional max retries override
            
        Returns:
            API response as dict
            
        Raises:
            APIError: On API errors
            TimeoutError: On timeout
        """
        timeout = timeout or self.INITIAL_TIMEOUT
        max_retries = max_retries if max_retries is not None else self.MAX_RETRIES
        url = f"{self.API_BASE_URL}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                # Calculate exponential backoff delay
                if attempt > 0:
                    delay = min(2 ** (attempt - 1), self.MAX_BACKOFF)
                    time.sleep(delay)
                
                response = requests.request(
                    method,
                    url,
                    json=json_data,
                    timeout=timeout
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise TimeoutError(f"API request timed out after {max_retries} attempts")
                logger.warning(f"Attempt {attempt + 1} timed out, retrying...")
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise APIError(f"API request failed: {str(e)}")
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}, retrying...")
    
    def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text from image using basic OCR.
        
        Args:
            image: Input image array
            
        Returns:
            Dict containing success status, extracted text and preprocessing images
            
        Raises:
            TimeoutError: If processing exceeds timeout
        """
        try:
            # Preprocess image
            preprocessed = self.pipeline.preprocess(image)
            
            # Store preprocessing images
            self.preprocessing_images = self.pipeline.intermediate_images
            
            # Convert image to base64
            success, buffer = cv2.imencode('.jpg', preprocessed)
            if not success:
                return {"success": False, "error": "Failed to encode image"}
            
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Make API request
            result = self._make_api_request(
                "POST",
                "/v1/chat/completions",
                json_data={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a precise OCR system. Extract and return ONLY the visible text from the image. Do not add any interpretation or context. Only return what you can actually read."
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "What text do you see in this image? ONLY return the text, nothing else."},
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
                }
            )
            
            # Extract text
            text = result["choices"][0]["message"]["content"].strip()
            
            return {
                "success": True,
                "text": text
            }
            
        except TimeoutError as e:
            logger.warning(f"Text extraction timed out: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _process_region(
        self, 
        region: TextRegion, 
        prompt: str,
        timeout: Optional[Tuple[float, float]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single region with retries and error handling.
        
        Args:
            region: Text region to process
            prompt: Prompt to use
            
        Returns:
            Dict with text and confidence if successful, None otherwise
        """
        if region.image is None or region.image.size == 0:
            return None
            
        try:
            # Convert image to base64
            success, buffer = cv2.imencode('.jpg', region.image)
            if not success:
                logger.warning("Failed to encode region image")
                return None
            
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Calculate remaining time for timeout
            api_timeout = timeout or self.INITIAL_TIMEOUT
            
            # Make API request with timeout
            result = self._make_api_request(
                "POST",
                "/v1/chat/completions",
                json_data={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a VHS cover text extractor. Only return the exact text requested, nothing else."
                        },
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
                    "temperature": 0.1,
                    "max_tokens": 50
                }
            )
            
            # Extract and validate text
            text = result["choices"][0]["message"]["content"].strip()
            if not text or len(text) > 200:  # Basic validation
                return None
                
            return {"text": text}
            
        except TimeoutError as e:
            logger.warning(f"Region processing timed out: {e}")
            raise  # Re-raise timeout for proper handling
        except APIError as e:
            logger.warning(f"Region processing failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing region: {e}")
            return None
            
    def extract_info(
        self, 
        image: Optional[np.ndarray], 
        category: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract specific information from image with optimized preprocessing.
        
        Args:
            image: Image array or None
            category: Category to extract (title, year, runtime, studio, director, cast, rating)
            timeout: Optional timeout in seconds
            
        Returns:
            Dict containing extracted text, confidence and validation info
        """
        # Input validation
        error_result = {
            "text": "",
            "confidence": 0.0,
            "category": category,
            "validated": False
        }
        
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            error_result["error"] = "Invalid image input"
            return error_result
            
        if not isinstance(category, str) or category not in {
            "title", "year", "runtime", "studio", "director", "cast", "rating"
        }:
            error_result["error"] = "Invalid category"
            return error_result
            
        try:
            # Save original image for debug if enabled
            if self.save_debug:
                self.save_debug_image(image, f"original_{category}")
            
            try:
                # Initialize region detector if needed
                if not hasattr(self, 'region_detector'):
                    self.region_detector = RegionDetector()
                
                # Preprocess image
                preprocessed = self.pipeline.preprocess(image)
                
                # Detect text regions
                regions = self.region_detector.detect(preprocessed)
                
            except Exception as e:
                logger.error(f"Preprocessing failed: {e}")
                error_result["error"] = f"Preprocessing error: {str(e)}"
                return error_result
            
            if self.save_debug:
                self.save_debug_image(preprocessed, f"preprocessed_{category}")
            
            # Enhanced category-specific prompts with preprocessing context
            base_prompts = {
                "title": "Extract movie title from this enhanced VHS cover image. Text has been preprocessed for optimal clarity. ONLY return the title text, nothing else.",
                "year": "Find the release year from this enhanced VHS cover image. Text visibility has been optimized. ONLY return the 4-digit year, nothing else.",
                "runtime": "Locate the runtime from this preprocessed VHS cover image. Text contrast has been enhanced. Return ONLY the number (e.g., if you see '116 minutes', return just '116').",
                "studio": "Find the studio/production company from this enhanced VHS cover image. Text has been optimized for readability. ONLY return the studio name, nothing else.",
                "director": "Extract the director name from this preprocessed VHS cover. Text clarity has been improved. Return ONLY the director's full name.",
                "cast": "Find actor names from this enhanced VHS cover image. Text has been processed for better visibility. ONLY return comma-separated names, nothing else.",
                "rating": "Locate the MPAA rating (G, PG, PG-13, R, or NC-17) on this preprocessed VHS cover. Text has been enhanced. Return ONLY the rating."
            }
            
            if not regions:
                error_result["error"] = "No text regions detected"
                return error_result
            
            # Process regions with enhanced confidence scoring
            best_result = error_result.copy()
            start_time = time.time()
            scored_results = []
            
            try:
                for region in regions[:3]:  # Try top 3 regions
                    # Check timeout
                    if timeout and (time.time() - start_time) > timeout:
                        raise TimeoutError(f"Region processing timed out after {timeout} seconds")
                    
                    # Build prompt with region-specific context
                    prompt = base_prompts[category]
                    
                    result = self._process_region(
                        region, 
                        prompt,
                        timeout=(2, timeout - (time.time() - start_time)) if timeout else None
                    )
                    if result:
                        # Basic confidence scoring
                        confidence = self.scorer.score_text(result["text"], category)
                        
                        scored_results.append({
                            "text": result["text"],
                            "confidence": confidence,
                            "category": category,
                            "validated": True,
                            "source": "lmstudio"
                        })
                        
                        # Early exit on very high confidence
                        if confidence >= 95:
                            break
                
                # Select best result from scored results
                if scored_results:
                    best_result = max(scored_results, key=lambda x: x["confidence"])
                
            except TimeoutError as e:
                logger.warning(f"Timeout during region processing: {e}")
                raise
            
            # Store preprocessing images and save for debug
            self.preprocessing_images = self.pipeline.intermediate_images
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
            
            error_result["error"] = str(e)
            return error_result
            
    def save_debug_image(self, image: Optional[np.ndarray], name: str, debug_dir: str = "debug_output"):
        """Save debug image."""
        if not self.save_debug or image is None:
            return
            
        try:
            debug_path = Path(debug_dir)
            debug_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = debug_path / f"{name}_{timestamp}.jpg"
            
            cv2.imwrite(str(path), image)
            logger.debug(f"Saved debug image: {path}")
        except Exception as e:
            logger.error(f"Failed to save debug image: {e}")
