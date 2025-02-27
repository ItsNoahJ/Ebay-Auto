"""
OpenCV utility functions for image processing.
"""
import cv2
import numpy as np
from typing import List, Tuple

def resize_image(image: np.ndarray, width: int = None, height: int = None) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio.
    
    Args:
        image: Input image
        width: Target width (optional)
        height: Target height (optional)
        
    Returns:
        Resized image
    """
    if width is None and height is None:
        return image
        
    h, w = image.shape[:2]
    if width is None:
        aspect = height / h
        width = int(w * aspect)
    elif height is None:
        aspect = width / w
        height = int(h * aspect)
        
    return cv2.resize(image, (width, height))

def apply_adaptive_contrast(
    image: np.ndarray,
    clip_limit: float = 3.0,
    grid_size: Tuple[int, int] = (8, 8),
    adaptive_method: int = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
) -> np.ndarray:
    """
    Apply adaptive contrast enhancement to image.
    
    Args:
        image: Input grayscale image
        clip_limit: Threshold for contrast limiting
        grid_size: Size of grid for histogram equalization
        adaptive_method: Method for adaptive processing
        
    Returns:
        Enhanced image
    """
    # Create CLAHE object
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
    
    # Apply adaptive equalization
    enhanced = clahe.apply(image)
    
    # Apply adaptive thresholding for improved text contrast
    mask = cv2.adaptiveThreshold(
        enhanced,
        255,
        adaptive_method,
        cv2.THRESH_BINARY,
        11,  # block size
        2    # C constant
    )
    
    # Combine original and thresholded image
    result = cv2.addWeighted(enhanced, 0.7, mask, 0.3, 0)
    
    return result

def enhance_image(
    image: np.ndarray,
    sharpen: bool = False,
    contrast: bool = True,
    denoise: bool = True,
    adaptive_contrast: bool = False  # New parameter
) -> np.ndarray:
    """
    Enhance image for better OCR with improved preprocessing pipeline.
    
    Args:
        image: Input image
        sharpen: Apply sharpening
        contrast: Enhance contrast
        denoise: Apply denoising
        adaptive_contrast: Use adaptive contrast enhancement
        
    Returns:
        Enhanced image
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Resize if image is too small
    min_dim = min(gray.shape[0], gray.shape[1])
    if min_dim < 1000:
        scale = 1000.0 / min_dim
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Basic noise reduction
    if denoise:
        gray = cv2.medianBlur(gray, 3)
    
    # Enhance contrast
    if contrast:
        if adaptive_contrast:
            # Use new adaptive contrast enhancement
            gray = apply_adaptive_contrast(gray)
        else:
            # Use traditional contrast enhancement
            gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
    
    # Simple sharpening
    if sharpen:
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        gray = cv2.filter2D(gray, -1, kernel)
    
    # Thresholding with small block size for better text detection
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        15,  # smaller block size
        5    # constant subtracted from mean
    )
    
    # Clean up noise and connect text components
    kernel = np.ones((2,2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    return binary

def detect_edges(image: np.ndarray) -> np.ndarray:
    """
    Detect edges in image.
    
    Args:
        image: Input image
        
    Returns:
        Edge image
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    # Blur and detect edges
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    return edges

def detect_rectangles(
    edges: np.ndarray,
    min_area: int = 1000,
    max_area: int = None,
    epsilon_factor: float = 0.02
) -> List[np.ndarray]:
    """
    Detect rectangles in edge image.
    
    Args:
        edges: Edge image
        min_area: Minimum contour area
        max_area: Maximum contour area
        epsilon_factor: Approximation accuracy factor
        
    Returns:
        List of rectangle contours
    """
    # Find contours
    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    rectangles = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        
        # Filter by area
        if area < min_area:
            continue
        if max_area and area > max_area:
            continue
            
        # Approximate contour
        epsilon = epsilon_factor * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        
        # Check if approximately rectangular (4 points)
        if len(approx) == 4:
            rectangles.append(approx)
            
    return rectangles

def detect_text_regions(
    image: np.ndarray,
    block_size: int = 11,
    c: int = 2
) -> List[Tuple[int, int, int, int]]:
    """
    Detect potential text regions in image.
    
    Args:
        image: Input image
        block_size: Block size for adaptive thresholding
        c: Constant for adaptive thresholding
        
    Returns:
        List of (x, y, w, h) bounding boxes
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    # Threshold
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block_size,
        c
    )
    
    # Find contours
    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Get bounding boxes
    boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Filter by size
        if w < 10 or h < 10:  # Too small
            continue
        if w > image.shape[1] * 0.9:  # Too wide
            continue
        if h > image.shape[0] * 0.9:  # Too tall
            continue
            
        boxes.append((x, y, w, h))
        
    return boxes

def draw_debug_image(
    image: np.ndarray,
    regions: List[dict]
) -> np.ndarray:
    """
    Draw debug visualization.
    
    Args:
        image: Input image
        regions: List of region data
        
    Returns:
        Debug image
    """
    debug = image.copy()
    
    for region in regions:
        # Draw region polygon
        cv2.drawContours(
            debug,
            [np.array(region["coords"])],
            -1,
            (0, 255, 0),
            2
        )
        
        # Draw text
        x, y = region["coords"][0][0]
        cv2.putText(
            debug,
            region["text"][:20] + "...",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )
        
    return debug
