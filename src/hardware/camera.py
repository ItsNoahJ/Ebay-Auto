"""
Camera interface module.
"""
import logging
import time
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

from ..config.settings import CAMERA_SETTINGS, STORAGE_PATHS

class Camera:
    """Camera interface."""
    
    def __init__(self):
        """Initialize camera."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self.device = None
        self.is_open = False
        
    def open(self) -> bool:
        """
        Open camera device.
        
        Returns:
            Success state
        """
        try:
            # Check if already open
            if self.is_open:
                return True
                
            # Open device
            self.device = cv2.VideoCapture(
                CAMERA_SETTINGS["device_id"]
            )
            
            if not self.device.isOpened():
                raise RuntimeError("Failed to open camera device")
                
            # Set resolution
            width = CAMERA_SETTINGS["resolution_width"]
            height = CAMERA_SETTINGS["resolution_height"]
            
            self.device.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.device.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Set auto focus
            if CAMERA_SETTINGS["auto_focus"]:
                self.device.set(
                    cv2.CAP_PROP_AUTOFOCUS,
                    1
                )
                
            # Set focus value
            if CAMERA_SETTINGS["focus_value"] is not None:
                self.device.set(
                    cv2.CAP_PROP_FOCUS,
                    CAMERA_SETTINGS["focus_value"]
                )
                
            # Set auto exposure
            if CAMERA_SETTINGS["auto_exposure"]:
                self.device.set(
                    cv2.CAP_PROP_AUTO_EXPOSURE,
                    1
                )
                
            # Set exposure value
            if CAMERA_SETTINGS["exposure_value"] is not None:
                self.device.set(
                    cv2.CAP_PROP_EXPOSURE,
                    CAMERA_SETTINGS["exposure_value"]
                )
                
            # Update state
            self.is_open = True
            
            return True
            
        except Exception as e:
            self.logger.exception("Open error")
            self.close()
            return False
            
    def close(self):
        """Close camera device."""
        # Release device
        if self.device is not None:
            self.device.release()
            
        # Update state
        self.device = None
        self.is_open = False
        
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read camera frame.
        
        Returns:
            Frame image if successful, None otherwise
        """
        try:
            # Check state
            if not self.is_open:
                return None
                
            # Read frame
            success, frame = self.device.read()
            
            if not success:
                return None
                
            return frame
            
        except Exception as e:
            self.logger.exception("Read error")
            return None
            
    def capture_image(self) -> Optional[str]:
        """
        Capture image.
        
        Returns:
            Path to saved image if successful, None otherwise
        """
        try:
            # Read frame
            frame = self.read_frame()
            
            if frame is None:
                return None
                
            # Create filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
            
            # Create path
            image_path = STORAGE_PATHS["images"] / filename
            image_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save image
            cv2.imwrite(str(image_path), frame)
            
            return str(image_path)
            
        except Exception as e:
            self.logger.exception("Capture error")
            return None
            
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get current resolution.
        
        Returns:
            Tuple of (width, height)
        """
        if not self.is_open:
            return (0, 0)
            
        width = int(self.device.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.device.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return (width, height)
        
    def __del__(self):
        """Clean up."""
        self.close()
