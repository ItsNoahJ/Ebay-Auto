"""
Image preview widget module.
"""
import logging
from pathlib import Path

import cv2
from PyQt6 import QtCore
from PyQt6.QtGui import QImage, QPixmap, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QLabel, QSizePolicy

from ..config.settings import GUI_SETTINGS

class ImagePreview(QLabel):
    """Image preview widget."""
    
    # Signals
    image_loaded = QtCore.pyqtSignal(str)
    
    def __init__(self):
        """Initialize widget."""
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self.current_image = None
        self.current_path = None
        
        # Configure widget
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        # Set maximum size to prevent infinite expansion
        self.setMaximumSize(800, 600)
        # Set minimum size for better UX
        self.setMinimumSize(200, 150)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Set placeholder text and style
        self.setText("Drag image here or click Open")
        self.setStyleSheet("""
            QLabel {
                color: rgba(0, 0, 0, 0.5);
                font-size: 13px;
                padding: 20px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 4px;
                background: white;
            }
        """)
        
    def load_image(self, image_path: str):
        """
        Load image file.
        
        Args:
            image_path: Path to image file
        """
        self.logger.info(f"Loading image: {image_path}")
        try:
            # Load image
            image = cv2.imread(image_path)
            
            if image is None:
                self.logger.error(f"Failed to load image: {image_path}")
                raise RuntimeError(
                    f"Failed to load image: {image_path}"
                )
                
            self.logger.info("Image loaded successfully")
                
            # Store image and path
            self.current_image = image
            self.current_path = image_path
            
            # Update preview
            self.logger.info("Updating preview...")
            self._update_preview()
            self.logger.info("Preview updated")
            
            # Emit signal
            self.logger.info(f"Emitting image_loaded signal with path: {image_path}")
            self.image_loaded.emit(image_path)
            self.logger.info("Signal emitted")
            
        except Exception as e:
            self.logger.exception("Load error")
            
    def _update_preview(self):
        """Update preview."""
        try:
            if self.current_image is None:
                return

            # Get widget dimensions
            widget_width = min(800, self.width())
            widget_height = min(600, self.height())
                
            # Convert to RGB
            rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
            
            # Calculate aspect ratio preserving dimensions
            img_height, img_width = rgb.shape[:2]
            scale = min(widget_width/img_width, widget_height/img_height)
            
            # Scale image to fit widget bounds
            if scale != 1.0:
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                rgb = cv2.resize(rgb, (new_width, new_height))
                
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
            
            # Scale to fit widget while maintaining aspect ratio
            scaled = pixmap.scaled(
                self.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation
            )
            
            # Update label
            self.setPixmap(scaled)
            
        except Exception as e:
            self.logger.exception("Update error")
            
    def clear(self):
        """Clear preview."""
        self.current_image = None
        self.current_path = None
        super().clear()
        
        # Reset placeholder with minimal style
        self.setText("Drag image here or click Open")
        self.setStyleSheet("""
            QLabel {
                color: rgba(0, 0, 0, 0.5);
                font-size: 13px;
                padding: 20px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 4px;
                background: white;
            }
        """)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        # Accept image files
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg'))
                   for url in urls):
                event.acceptProposedAction()
                self.setStyleSheet("""
                    QLabel {
                        color: #666;
                        font-size: 14px;
                        padding: 20px;
                        border: 1px solid #28a745;
                        border-radius: 8px;
                        background: #f8f9fa;
                    }
                """)

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        # Reset style
        self.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                padding: 20px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                background: #f8f9fa;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        # Get dropped file
        urls = event.mimeData().urls()
        if urls:
            # Get first image file
            image_paths = [
                url.toLocalFile() for url in urls
                if url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg'))
            ]
            if image_paths:
                self.load_image(image_paths[0])

        # Reset style
        self.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                padding: 20px;
                border: 2px dashed #ccc;
                border-radius: 8px;
                background: #f8f9fa;
            }
        """)

    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        
        # Update preview on resize
        if self.current_image is not None:
            self._update_preview()
