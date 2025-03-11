"""
OpenCV utility functions.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

def load_image(path: str) -> Optional[np.ndarray]:
    """
    Load image from path.
    
    Args:
        path: Path to image file
        
    Returns:
        Image array or None if loading fails
    """
    try:
        image = cv2.imread(path)
        if image is None:
            logger.error(f"Failed to load image: {path}")
            return None
            
        return image
    except Exception as e:
        logger.error(f"Error loading image {path}: {e}")
        return None

def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert image to grayscale if needed."""
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        return gray
    except Exception as e:
        logger.error(f"Grayscale conversion error: {e}")
        return image
        
def resize_image(image: np.ndarray, target_width: int = 1024) -> np.ndarray:
    """Resize image maintaining aspect ratio."""
    try:
        h, w = image.shape[:2]
        if w > target_width:
            ratio = target_width / w
            new_size = (target_width, int(h * ratio))
            resized = cv2.resize(image, new_size)
            return resized
        return image
    except Exception as e:
        logger.error(f"Resize error: {e}")
        return image
        
def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast using advanced adaptive techniques.
    
    Args:
        image: Input grayscale image
        
    Returns:
        Contrast enhanced image with improved text visibility
    """
    try:
        # Initial brightness normalization using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        clahe_result = clahe.apply(image)
        
        # Local contrast enhancement
        kernel_size = 15
        local_mean = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        local_std = cv2.GaussianBlur((image - local_mean)**2, (kernel_size, kernel_size), 0)**0.5
        
        # Enhance local contrast where std is low (flat regions)
        alpha = np.clip(1.5 - local_std / local_std.max(), 0.8, 1.5)
        enhanced = cv2.addWeighted(image, alpha.mean(), clahe_result, 2-alpha.mean(), 0)
        
        # Fine-tune contrast using bilateral filter
        bilateral = cv2.bilateralFilter(enhanced, d=5, sigmaColor=10, sigmaSpace=10)
        
        # Apply second CLAHE pass with milder parameters
        clahe_mild = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))
        result = clahe_mild.apply(bilateral)
        
        # Blend results based on text clarity
        text_clarity_orig = estimate_text_clarity(enhanced)
        text_clarity_new = estimate_text_clarity(result)
        
        if text_clarity_new > text_clarity_orig * 1.2:
            return result
        elif text_clarity_new > text_clarity_orig * 0.8:
            # Weighted blend
            alpha = text_clarity_new / (text_clarity_orig + text_clarity_new)
            return cv2.addWeighted(enhanced, 1-alpha, result, alpha, 0)
        else:
            return enhanced
        
    except Exception as e:
        logger.error(f"Contrast enhancement error: {e}")
        return image

def estimate_text_clarity(image: np.ndarray) -> float:
    """
    Estimate text clarity in an image using edge detection.
    
    Args:
        image: Grayscale image
        
    Returns:
        Clarity score (higher is better)
    """
    try:
        # Apply Sobel edge detection
        grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        
        # Calculate gradient magnitude
        gradient = np.sqrt(grad_x**2 + grad_y**2)
        
        # Focus on strong edges likely to be text
        strong_edges = gradient > np.mean(gradient) + np.std(gradient)
        
        # Calculate clarity score
        edge_strength = np.mean(gradient[strong_edges]) if np.any(strong_edges) else 0
        edge_count = np.sum(strong_edges) / image.size  # Normalized edge count
        
        return edge_strength * edge_count
        
    except Exception as e:
        logger.error(f"Text clarity estimation error: {e}")
        return 0.0

def denoise_image(image: np.ndarray) -> np.ndarray:
    """
    Apply advanced adaptive denoising optimized for text preservation.
    
    Args:
        image: Input grayscale or color image
        
    Returns:
        Denoised image with preserved text edges
    """
    try:
        # Ensure uint8 type
        if image.dtype != np.uint8:
            image = cv2.convertScaleAbs(image)
            
        # Calculate local noise levels using sliding window
        patch_size = 7
        noise_map = np.zeros_like(image, dtype=np.float32)
        
        # Pad image for window operations
        padded = cv2.copyMakeBorder(image, patch_size//2, patch_size//2, patch_size//2, patch_size//2, cv2.BORDER_REFLECT)
        
        # Calculate local noise for each pixel
        h, w = image.shape[:2]
        for i in range(h):
            for j in range(w):
                patch = padded[i:i+patch_size, j:j+patch_size]
                noise_map[i,j] = np.std(patch)
                
        # Normalize noise map
        noise_map = cv2.normalize(noise_map, None, 0, 1, cv2.NORM_MINMAX)
        
        # Calculate edge mask to preserve text
        grad_x = cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3)
        edge_mask = np.sqrt(grad_x**2 + grad_y**2)
        edge_mask = cv2.normalize(edge_mask, None, 0, 1, cv2.NORM_MINMAX)
        
        # Combine noise map and edge mask
        denoising_strength = 1 - (edge_mask * 0.7 + noise_map * 0.3)
        
        # Adaptive bilateral filtering
        sigma_color_base = 10
        sigma_space_base = 10
        
        # Apply bilateral filter with adapted parameters
        bilateral = cv2.bilateralFilter(
            image, 
            d=5,
            sigmaColor=sigma_color_base * (1 + denoising_strength.mean()),
            sigmaSpace=sigma_space_base
        )
        
        # For very noisy regions, apply additional targeted filtering
        if np.mean(noise_map) > 0.5:
            # Second pass with stronger parameters in noisy areas
            mask = noise_map > 0.7
            if np.any(mask):
                strong_denoise = cv2.bilateralFilter(
                    bilateral,
                    d=7,
                    sigmaColor=sigma_color_base * 2,
                    sigmaSpace=sigma_space_base * 1.5
                )
                # Convert noise_map to proper format for blending
                blend_weight = noise_map.astype(np.float32)
                bilateral = cv2.addWeighted(
                    bilateral,
                    1.0 - blend_weight.mean(),
                    strong_denoise,
                    blend_weight.mean(),
                    0
                )
        
        return bilateral.astype(np.uint8)
    except Exception as e:
        logger.error(f"Denoising error: {e}")
        return image

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image with advanced optimization for text extraction.
    
    Args:
        image: Input image array
        
    Returns:
        Preprocessed image array optimized for OCR with enhanced text clarity
    """
    try:
        # Convert to grayscale
        gray = convert_to_grayscale(image)
        
        # Analyze image characteristics
        initial_std = np.std(gray)
        initial_mean = np.mean(gray)
        initial_clarity = estimate_text_clarity(gray)
        
        # Adaptive resize based on image quality
        target_width = 2048 if initial_clarity > 0.1 else 1600
        resized = resize_image(gray, target_width=target_width)
        
        # Enhanced contrast first to improve text visibility
        enhanced = enhance_contrast(resized)
        
        # Apply selective denoising based on local noise levels
        if initial_std < 40:
            denoised = denoise_image(enhanced)
            # Verify denoising didn't harm text clarity
            denoised_clarity = estimate_text_clarity(denoised)
            if denoised_clarity >= initial_clarity * 0.9:
                enhanced = denoised
        
        # Apply additional contrast enhancement if needed
        enhanced_clarity = estimate_text_clarity(enhanced)
        if enhanced_clarity < initial_clarity * 0.9:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))
            clahe_result = clahe.apply(enhanced)
            # Blend based on clarity
            blend_alpha = min(enhanced_clarity / initial_clarity, 0.7)
            enhanced = cv2.addWeighted(enhanced, 1.0 - blend_alpha, clahe_result, blend_alpha, 0)
        
        # Normalize to optimal range for OCR based on image characteristics
        target_mean = 135 if initial_mean < 100 else (120 if initial_mean > 200 else 127)
        target_std = 45 if initial_mean < 100 else (35 if initial_mean > 200 else 40)
        normalized = normalize_image(enhanced, target_mean=target_mean, target_std=target_std)
        
        final_clarity = estimate_text_clarity(normalized)
        if final_clarity < initial_clarity * 0.9:
            # Apply adaptive sharpening
            kernel_size = 3
            kernel = np.zeros((kernel_size, kernel_size), np.float32)
            kernel[1,1] = 1.5
            kernel[0,1] = kernel[2,1] = kernel[1,0] = kernel[1,2] = -0.25
            sharpened = cv2.filter2D(normalized, -1, kernel)
            
            # Blend sharpened result if it improves clarity
            sharp_clarity = estimate_text_clarity(sharpened)
            if sharp_clarity > final_clarity:
                blend_ratio = min((sharp_clarity - final_clarity) / final_clarity, 0.5)
                normalized = cv2.addWeighted(normalized, 1.0 - blend_ratio, sharpened, blend_ratio, 0)
        
        return normalized
        
    except Exception as e:
        logger.error(f"Preprocessing error: {e}")
        return image

def normalize_image(image: np.ndarray, target_mean: float = 127, target_std: float = 50) -> np.ndarray:
    """
    Normalize image with advanced histogram matching.
    
    Args:
        image: Input image array
        target_mean: Target mean intensity
        target_std: Target standard deviation
        
    Returns:
        Normalized image array
    """
    try:
        # Calculate current statistics
        mean = np.mean(image)
        std = np.std(image)
        
        # Normalize to target statistics
        normalized = ((image - mean) * (target_std / std) + target_mean)
        normalized = np.clip(normalized, 0, 255).astype(np.uint8)
        
        return normalized
        
    except Exception as e:
        logger.error(f"Normalization error: {e}")
        return image

def extract_text_regions(image: np.ndarray) -> list:
    """
    Extract potential text regions from image.
    
    Args:
        image: Input image array
        
    Returns:
        List of (x,y,w,h) region tuples
    """
    try:
        # Find contours
        contours, _ = cv2.findContours(
            image,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Get bounding rectangles
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter small regions
            if w > 20 and h > 20:
                regions.append((x, y, w, h))
                
        return regions
        
    except Exception as e:
        logger.error(f"Region extraction error: {e}")
        return []
