"""
Custom GUI widgets.
"""
import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QFrame
)

class CameraPreviewWidget(QWidget):
    """Camera preview widget."""
    
    capture_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize widget."""
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create preview label
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        layout.addWidget(self.preview)
        
        # Create capture button
        self.capture_button = QPushButton("Capture")
        self.capture_button.clicked.connect(self.capture_signal.emit)
        layout.addWidget(self.capture_button)
        
        self.setLayout(layout)
        
    def update_preview(self, frame: np.ndarray):
        """
        Update preview image.
        
        Args:
            frame: Image frame
        """
        if frame is None:
            return
            
        # Convert frame
        height, width = frame.shape[:2]
        bytes_per_line = 3 * width
        
        image = QImage(
            frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888
        ).rgbSwapped()
        
        # Scale to fit
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(
            self.preview.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.preview.setPixmap(scaled)

class ResultsWidget(QWidget):
    """Results display widget."""
    
    def __init__(self, parent=None):
        """Initialize widget."""
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create image preview
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        layout.addWidget(self.image)
        
        # Create info panel
        info_panel = QFrame()
        info_panel.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        
        info_layout = QVBoxLayout()
        
        self.title = QLabel()
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(self.title)
        
        self.year = QLabel()
        info_layout.addWidget(self.year)
        
        self.rating = QLabel()
        info_layout.addWidget(self.rating)
        
        self.genres = QLabel()
        info_layout.addWidget(self.genres)
        
        info_panel.setLayout(info_layout)
        layout.addWidget(info_panel)
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Results")
        button_layout.addWidget(self.save_button)
        
        self.clear_button = QPushButton("Clear")
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def update_results(self, results: dict):
        """
        Update results display.
        
        Args:
            results: Processing results
        """
        if not results or not results.get("success"):
            self.clear()
            return
            
        # Update movie info
        movie = results["movie_data"]
        
        self.title.setText(movie["title"])
        self.year.setText(f"Year: {movie['release_date'][:4]}")
        self.rating.setText(f"Rating: {movie.get('vote_average', 'N/A')}")
        
        genres = [g["name"] for g in movie.get("genres", [])]
        self.genres.setText(f"Genres: {', '.join(genres)}")
        
        # Update debug image if available
        if "debug_image" in results:
            self.set_image(results["debug_image"])
            
    def set_image(self, image_path: str):
        """
        Set preview image.
        
        Args:
            image_path: Path to image file
        """
        # Load image
        image = cv2.imread(image_path)
        
        if image is not None:
            # Convert to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Create QImage
            height, width = image.shape[:2]
            bytes_per_line = 3 * width
            
            qimage = QImage(
                image.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGB888
            )
            
            # Scale to fit
            pixmap = QPixmap.fromImage(qimage)
            scaled = pixmap.scaled(
                self.image.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.image.setPixmap(scaled)
            
    def clear(self):
        """Clear results display."""
        self.image.clear()
        self.title.clear()
        self.year.clear()
        self.rating.clear()
        self.genres.clear()
