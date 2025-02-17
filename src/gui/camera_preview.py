"""
Camera preview widget module.
"""
import logging
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy

from ..config.settings import CAMERA_SETTINGS, GUI_SETTINGS
from ..hardware.camera import Camera

class CameraPreview(QLabel):
    """Camera preview widget."""
    
    # Signals
    image_captured = pyqtSignal(str)
    
    def __init__(self):
        """Initialize widget."""
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self.camera = Camera()
        self.preview_timer = None
        self.current_image = None
        
        # Configure widget
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
    def start_preview(self) -> bool:
        """
        Start camera preview.
        
        Returns:
            Success state
        """
        try:
            # Open camera
            if not self.camera.open():
                return False
                
            # Create timer
            self.preview_timer = QTimer()
            self.preview_timer.timeout.connect(self._update_preview)
            
            # Calculate interval
            interval = int(1000 / GUI_SETTINGS["preview_fps"])
            self.preview_timer.start(interval)
            
            return True
            
        except Exception as e:
            self.logger.exception("Preview error")
            return False
            
    def stop_preview(self):
        """Stop camera preview."""
        # Stop timer
        if self.preview_timer:
            self.preview_timer.stop()
            self.preview_timer = None
            
        # Close camera
        self.camera.close()
        
        # Clear preview
        self.clear()
        
    def capture_image(self):
        """Capture current image."""
        try:
            # Capture image
            image_path = self.camera.capture_image()
            
            if image_path:
                # Load captured image
                self.load_image(image_path)
                
                # Emit signal
                self.image_captured.emit(image_path)
                
        except Exception as e:
            self.logger.exception("Capture error")
            
    def load_image(self, image_path: str):
        """
        Load image file.
        
        Args:
            image_path: Path to image file
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            
            if image is None:
                raise RuntimeError(
                    f"Failed to load image: {image_path}"
                )
                
            # Store image
            self.current_image = image
            
            # Update preview
            self._update_preview()
            
        except Exception as e:
            self.logger.exception("Load error")
            
    def _update_preview(self):
        """Update preview frame."""
        try:
            # Get frame
            if self.preview_timer:
                frame = self.camera.read_frame()
            else:
                frame = self.current_image
                
            if frame is None:
                return
                
            # Convert to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Scale frame
            scale = GUI_SETTINGS["preview_scale"]
            
            if scale != 1.0:
                height = int(rgb.shape[0] * scale)
                width = int(rgb.shape[1] * scale)
                rgb = cv2.resize(rgb, (width, height))
                
            # Create QImage
            height, width = rgb.shape[:2]
            bytes_per_line = 3 * width
            
            image = QImage(
                rgb.data,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )
            
            # Create pixmap
            pixmap = QPixmap.fromImage(image)
            
            # Update label
            self.setPixmap(pixmap)
            
        except Exception as e:
            self.logger.exception("Update error")
            
    def clear(self):
        """Clear preview."""
        self.current_image = None
        super().clear()
