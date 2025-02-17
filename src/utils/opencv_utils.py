"""
OpenCV utility functions.
"""
from typing import List, Tuple

import cv2
import numpy as np

def resize_image(
    image: np.ndarray,
    width: int = None,
    height: int = None
) -> np.ndarray:
    """
    Resize image maintaining aspect ratio.
    
    Args:
        image: Input image
        width: Target width
        height: Target height
        
    Returns:
        Resized image
    """
    # Get dimensions
    h, w = image.shape[:2]
    
    # Calculate new dimensions
    if width is not None and height is not None:
        # Both dimensions specified
        new_w = width
        new_h = height
    elif width is not None:
        # Width specified, maintain ratio
        ratio = width / w
        new_w = width
        new_h = int(h * ratio)
    elif height is not None:
        # Height specified, maintain ratio
        ratio = height / h
        new_h = height
        new_w = int(w * ratio)
    else:
        # No resize needed
        return image
        
    # Resize image
    return cv2.resize(
        image,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA
    )
    
def detect_edges(image: np.ndarray) -> np.ndarray:
    """
    Detect edges in image.
    
    Args:
        image: Input image
        
    Returns:
        Edge detection result
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    # Blur image
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Detect edges
    edges = cv2.Canny(blurred, 50, 150)
    
    # Clean up
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
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
        edges: Edge detection result
        min_area: Minimum contour area
        max_area: Maximum contour area
        epsilon_factor: Approximation accuracy factor
        
    Returns:
        List of rectangle contours
    """
    # Find contours
    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Process contours
    rectangles = []
    
    for cnt in contours:
        # Get area
        area = cv2.contourArea(cnt)
        
        # Check area
        if area < min_area:
            continue
            
        if max_area and area > max_area:
            continue
            
        # Approximate contour
        epsilon = epsilon_factor * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        
        # Check if rectangle (4 corners)
        if len(approx) == 4:
            rectangles.append(approx)
            
    return rectangles
    
def detect_text_regions(
    image: np.ndarray,
    block_size: int = 11,
    c: int = 9
) -> List[Tuple[int, int, int, int]]:
    """
    Detect text regions using adaptive thresholding.
    
    Args:
        image: Input image
        block_size: Block size for adaptive threshold
        c: Constant subtracted from mean
        
    Returns:
        List of region bounding boxes (x, y, w, h)
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    # Apply adaptive threshold
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
        boxes.append((x, y, w, h))
        
    return boxes
    
def enhance_image(image: np.ndarray) -> np.ndarray:
    """
    Enhance image for OCR.
    
    Args:
        image: Input image
        
    Returns:
        Enhanced image
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Increase contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Threshold
    _, thresh = cv2.threshold(
        enhanced,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    
    return thresh
    
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
    # Create copy
    debug = image.copy()
    
    # Draw regions
    for region in regions:
        # Get contour
        contour = np.array(region["coords"])
        
        # Draw rectangle
        cv2.drawContours(
            debug,
            [contour],
            -1,
            (0, 255, 0),
            2
        )
        
        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)
        
        # Draw text
        cv2.putText(
            debug,
            f"Text: {len(region['text'])} chars",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )
        
    return debug
