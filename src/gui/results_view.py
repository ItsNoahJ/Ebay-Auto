"""
Results view widget module.
"""
import json
import logging
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QLabel,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

class ResultsView(QTabWidget):
    """Results view widget."""
    
    def __init__(self):
        """Initialize widget."""
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self.current_results = None
        
        # Create tabs
        self._create_vision_tab()
        self._create_text_tab()
        self._create_movie_tab()
        self._create_debug_tab()
        
    def _create_vision_tab(self):
        """Create vision data tab."""
        # Create tab
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create text area
        self.vision_text = QTextEdit()
        self.vision_text.setReadOnly(True)
        layout.addWidget(self.vision_text)
        
        # Add tab
        self.addTab(tab, "Vision")
        
    def _create_text_tab(self):
        """Create extracted text tab."""
        # Create tab
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create text area
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        
        # Add tab
        self.addTab(tab, "Text")
        
    def _create_movie_tab(self):
        """Create movie data tab."""
        # Create tab
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create text area
        self.movie_text = QTextEdit()
        self.movie_text.setReadOnly(True)
        layout.addWidget(self.movie_text)
        
        # Add tab
        self.addTab(tab, "Movie")
        
    def _create_debug_tab(self):
        """Create debug visualization tab."""
        # Create tab
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Create image label
        self.debug_image = QLabel()
        self.debug_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(self.debug_image)
        
        # Add tab
        self.addTab(tab, "Debug")
        
    def update_results(self, results: dict):
        """
        Update results display.
        
        Args:
            results: Processing results
        """
        try:
            # Store results
            self.current_results = results
            
            # Update vision data
            vision_data = results["vision_data"]
            text = (
                f"Image Size: {vision_data['image_size']}\n"
                f"Sharpness: {vision_data['sharpness']:.1f}\n"
                f"Rectangles: {vision_data['rectangles']}\n"
                f"Text Regions: {vision_data['text_regions']}\n"
                f"Processing Time: {vision_data['processing_time']:.2f}s"
            )
            self.vision_text.setText(text)
            
            # Update extracted text
            if results["extracted_titles"]:
                text = "\n\n".join(results["extracted_titles"])
                self.text_area.setText(text)
            else:
                self.text_area.setText("No text extracted")
                
            # Update movie data
            movie = results["movie_data"]
            if movie:
                text = []
                
                # Basic info
                text.append(f"Title: {movie['title']}")
                
                if "release_date" in movie:
                    text.append(f"Year: {movie['release_date'][:4]}")
                    
                if "vote_average" in movie:
                    text.append(f"Rating: {movie['vote_average']:.1f}/10")
                    
                # Genres
                if "genres" in movie and movie["genres"]:
                    genres = [g["name"] for g in movie["genres"]]
                    text.append(f"Genres: {', '.join(genres)}")
                    
                # Overview
                if "overview" in movie:
                    text.append(f"\nOverview:\n{movie['overview']}")
                    
                self.movie_text.setText("\n".join(text))
            else:
                self.movie_text.setText("No movie data")
                
            # Update debug image
            if "debug_image" in results:
                pixmap = QPixmap(results["debug_image"])
                if not pixmap.isNull():
                    self.debug_image.setPixmap(pixmap)
                    
        except Exception as e:
            self.logger.exception("Update error")
            
    def save_results(self, json_path: str):
        """
        Save results to JSON file.
        
        Args:
            json_path: Output file path
        """
        if not self.current_results:
            return
            
        # Create directory
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        with open(json_path, "w") as f:
            json.dump(self.current_results, f, indent=2)
