"""
Widget for displaying OCR results and preprocessing images.
"""
import logging
from typing import Dict, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QTextEdit, QProgressBar, QScrollArea)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)

class ResultsView(QWidget):
    """Widget for displaying OCR results with confidence visualization."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize ResultsView widget."""
        super().__init__(parent)
        self.stage_labels: Dict[str, QLabel] = {}
        self.confidence_bars: Dict[str, QProgressBar] = {}
        self.text_edit = None
        self.preprocessing_images: Dict[str, QPixmap] = {}
        self.setup_ui()
        self.clear()  # Initialize with empty state
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout()
        
        # Text results area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        # Preprocessing images scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QHBoxLayout()
        
        # Create image preview for each stage
        for stage in ["Original", "Grayscale", "Enhanced", "Text"]:
            stage_widget = QWidget()
            stage_layout = QVBoxLayout()
            
            # Stage label
            stage_label = QLabel(stage)
            stage_layout.addWidget(stage_label)
            
            # Image label
            image_label = QLabel()
            image_label.setMinimumSize(200, 200)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stage_layout.addWidget(image_label)
            
            stage_widget.setLayout(stage_layout)
            scroll_layout.addWidget(stage_widget)
            
            # Store reference to image label
            self.stage_labels[stage] = image_label
            
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Confidence visualization area
        confidence_layout = QHBoxLayout()
        
        # Initialize confidence progress bars
        confidence_widget = QWidget()
        confidence_grid = QVBoxLayout()
        
        for field in ["title"]:  # Keep only title since that's what we're currently extracting
            field_layout = QHBoxLayout()
            
            # Field label
            label = QLabel(field.title())
            field_layout.addWidget(label)
            
            # Confidence bar
            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(100)
            field_layout.addWidget(bar)
            
            confidence_grid.addLayout(field_layout)
            self.confidence_bars[field] = bar
            
        confidence_widget.setLayout(confidence_grid)
        confidence_layout.addWidget(confidence_widget)
        layout.addLayout(confidence_layout)
        
        self.setLayout(layout)
        
    def update_results(self, results: Dict) -> None:
        """Update displayed results.
        
        Args:
            results: Dictionary containing OCR results and confidence scores
        """
        if not results.get("success", False):
            self.text_edit.setText(f"Error: {results.get('error', 'Unknown error')}")
            return
            
        # Update text results
        vision_data = results.get("vision_data", {})
        text_output = []
        
        for field, value in vision_data.items():
            if field != "confidence":
                text_output.append(f"{field.title()}: {value}")
                
        self.text_edit.setText("\n".join(text_output))
        
        # Update confidence bars
        confidence_data = vision_data.get("confidence", {})
        for field, score in confidence_data.items():
            self.update_confidence_bar(field, score)
            
    def update_preprocessing_image(self, stage: str, pixmap: QPixmap) -> None:
        """Update preprocessing stage image.
        
        Args:
            stage: Stage name
            pixmap: Image as QPixmap
        """
        if stage in self.stage_labels:
            label = self.stage_labels[stage]
            scaled_pixmap = pixmap.scaled(
                label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            label.setPixmap(scaled_pixmap)
            self.preprocessing_images[stage] = pixmap
            
    def get_stage_image(self, stage: str) -> Optional[QPixmap]:
        """Get preprocessing stage image.
        
        Args:
            stage: Stage name
            
        Returns:
            QPixmap if image exists for stage, None otherwise
        """
        return self.preprocessing_images.get(stage)
            
    def clear(self) -> None:
        """Clear all results and images."""
        self.text_edit.clear()
        for label in self.stage_labels.values():
            label.clear()
        self.preprocessing_images.clear()
        for bar in self.confidence_bars.values():
            bar.setValue(0)
            
    def update_confidence_bar(self, field: str, score: float) -> None:
        """Update confidence bar for a field.
        
        Args:
            field: Field name
            score: Confidence score (0-1)
        """
        if field not in self.confidence_bars:
            return
            
        bar = self.confidence_bars[field]
        value = int(score * 100)
        bar.setValue(value)
        
        # Color coding
        if score >= 0.9:
            color = "green"
        elif score >= 0.7:
            color = "blue"
        elif score >= 0.5:
            color = "yellow"
        else:
            color = "red"
            
        bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid grey;
                border-radius: 2px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
