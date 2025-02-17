"""
Main GUI application module.
"""
import os
import cv2
import time
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

from ..config.settings import GUI_SETTINGS, CAMERA_SETTINGS, STORAGE_DIR
from ..models.coordinator import ProcessingCoordinator
from ..hardware.camera import CameraDevice
from .camera_preview import CameraPreview
from .results_view import ResultsView

class VHSScannerApp(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize window."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.coordinator = ProcessingCoordinator()
        self.camera = CameraDevice()
        self.preview = None
        self.results = None
        
        # Setup UI
        self.setup_ui()
        
        # Connect camera
        if not self.connect_camera():
            QMessageBox.warning(
                self,
                "Camera Error",
                "Failed to connect to camera device"
            )
            
    def setup_ui(self):
        """Setup user interface."""
        # Configure window
        self.setWindowTitle(GUI_SETTINGS["window_title"])
        self.resize(
            GUI_SETTINGS["window_width"],
            GUI_SETTINGS["window_height"]
        )
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Create layout
        layout = QHBoxLayout(central)
        layout.setSpacing(GUI_SETTINGS["spacing"])
        layout.setContentsMargins(
            GUI_SETTINGS["margin"],
            GUI_SETTINGS["margin"],
            GUI_SETTINGS["margin"],
            GUI_SETTINGS["margin"]
        )
        
        # Create preview section
        preview_section = QWidget()
        preview_layout = QVBoxLayout(preview_section)
        preview_layout.setSpacing(GUI_SETTINGS["spacing"])
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create camera preview
        self.preview = CameraPreview()
        preview_layout.addWidget(self.preview)
        
        # Create capture button
        self.capture_button = QPushButton("Capture")
        self.capture_button.clicked.connect(self.capture_image)
        preview_layout.addWidget(self.capture_button)
        
        # Create load button
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)
        preview_layout.addWidget(self.load_button)
        
        # Add preview section
        layout.addWidget(preview_section)
        
        # Create results section
        results_section = QWidget()
        results_layout = QVBoxLayout(results_section)
        results_layout.setSpacing(GUI_SETTINGS["spacing"])
        results_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create results view
        self.results = ResultsView()
        results_layout.addWidget(self.results)
        
        # Create progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        results_layout.addWidget(self.progress)
        
        # Add results section
        layout.addWidget(results_section)
        
        # Set section sizes
        layout.setStretch(0, 1)  # Preview
        layout.setStretch(1, 1)  # Results
        
        # Apply theme
        self.apply_theme()
        
    def apply_theme(self):
        """Apply GUI theme."""
        # Get theme colors
        theme = GUI_SETTINGS["themes"][GUI_SETTINGS["theme"]]
        
        # Create stylesheet
        style = f"""
            QMainWindow {{
                background-color: {theme["background"]};
                color: {theme["foreground"]};
            }}
            
            QWidget {{
                background-color: {theme["background"]};
                color: {theme["foreground"]};
            }}
            
            QPushButton {{
                background-color: {theme["accent"]};
                color: {theme["background"]};
                border: none;
                padding: 8px;
                border-radius: 4px;
            }}
            
            QPushButton:hover {{
                background-color: {theme["foreground"]};
            }}
            
            QProgressBar {{
                border: 2px solid {theme["accent"]};
                border-radius: 4px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {theme["accent"]};
            }}
        """
        
        self.setStyleSheet(style)
        
    def connect_camera(self) -> bool:
        """
        Connect to camera device.
        
        Returns:
            True if successful
        """
        try:
            # Open camera
            if not self.camera.open():
                return False
                
            # Start preview
            self.camera.start_preview(
                on_frame=self.preview.update_frame,
                on_error=self.handle_camera_error
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Camera connection error: {e}")
            return False
            
    def capture_image(self):
        """Capture image from camera."""
        try:
            # Capture frame
            result = self.camera.capture_frame()
            
            if not result:
                raise RuntimeError("Failed to capture frame")
                
            frame, success = result
            
            if not success:
                raise RuntimeError("Frame capture failed")
                
            # Save image
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            image_path = STORAGE_DIR / "images" / f"capture_{timestamp}.jpg"
            
            cv2.imwrite(str(image_path), frame)
            
            # Process image
            self.process_image(str(image_path))
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Capture Error",
                f"Failed to capture image: {e}"
            )
            
    def load_image(self):
        """Load image from file."""
        try:
            # Show file dialog
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Load Image",
                str(STORAGE_DIR / "images"),
                "Images (*.jpg *.jpeg *.png);;All Files (*.*)"
            )
            
            if not path:
                return
                
            # Process image
            self.process_image(path)
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load image: {e}"
            )
            
    def process_image(self, image_path: str):
        """
        Process tape image.
        
        Args:
            image_path: Path to image file
        """
        try:
            # Show progress
            self.progress.setRange(0, 0)
            self.progress.show()
            
            # Disable buttons
            self.capture_button.setEnabled(False)
            self.load_button.setEnabled(False)
            
            # Process image
            results = self.coordinator.process_tape(
                image_path,
                debug=True
            )
            
            # Hide progress
            self.progress.hide()
            
            # Enable buttons
            self.capture_button.setEnabled(True)
            self.load_button.setEnabled(True)
            
            if not results["success"]:
                raise RuntimeError(
                    results.get("error", "Unknown error")
                )
                
            # Show results
            self.results.show_results(results)
            
            # Show debug image
            if results.get("debug_image"):
                debug_path = results["debug_image"]
                image = cv2.imread(debug_path)
                
                if image is not None:
                    self.preview.update_frame(image)
                    
        except Exception as e:
            # Hide progress
            self.progress.hide()
            
            # Enable buttons
            self.capture_button.setEnabled(True)
            self.load_button.setEnabled(True)
            
            QMessageBox.warning(
                self,
                "Processing Error",
                f"Failed to process image: {e}"
            )
            
    def handle_camera_error(self, error: str):
        """
        Handle camera error.
        
        Args:
            error: Error message
        """
        QMessageBox.warning(
            self,
            "Camera Error",
            error
        )
        
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            # Close camera
            self.camera.close()
            
        except Exception:
            pass
            
        # Accept event
        event.accept()
