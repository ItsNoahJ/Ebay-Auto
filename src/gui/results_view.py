"""
Results view widget module.
"""
import json
import logging
from pathlib import Path

from PyQt6 import QtCore
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QLabel,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
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
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(scroll)
        
        # Create container widget
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # Create text area
        self.vision_text = QPlainTextEdit()
        self.vision_text.setReadOnly(True)
        self.vision_text.setPlaceholderText("No image processed yet")
        self.vision_text.setMinimumHeight(200)
        self.vision_text.setStyleSheet(
            "QPlainTextEdit { background-color: #f8f9fa; padding: 10px; }"
        )
        container_layout.addWidget(self.vision_text)
        container_layout.addStretch()
        
        scroll.setWidget(container)
        
        # Add tab
        self.addTab(tab, "Vision Data")
        
    def _create_text_tab(self):
        """Create extracted text tab."""
        # Create tab
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(scroll)
        
        # Create container widget
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # Create text area
        self.text_area = QPlainTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlaceholderText("No text extracted yet")
        self.text_area.setMinimumHeight(200)
        self.text_area.setStyleSheet(
            "QPlainTextEdit { background-color: #f8f9fa; padding: 10px; }"
        )
        container_layout.addWidget(self.text_area)
        container_layout.addStretch()
        
        scroll.setWidget(container)
        
        # Add tab
        self.addTab(tab, "Extracted Text")
        
    def _create_movie_tab(self):
        """Create movie data tab."""
        # Create tab
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(scroll)
        
        # Create container widget
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # Create text area
        self.movie_text = QPlainTextEdit()
        self.movie_text.setReadOnly(True)
        self.movie_text.setPlaceholderText("No movie data found")
        self.movie_text.setMinimumHeight(200)
        self.movie_text.setStyleSheet(
            "QPlainTextEdit { background-color: #f8f9fa; padding: 10px; }"
        )
        container_layout.addWidget(self.movie_text)
        container_layout.addStretch()
        
        scroll.setWidget(container)
        
        # Add tab
        self.addTab(tab, "Movie Info")
        
    def _create_debug_tab(self):
        """Create debug visualization tab."""
        # Create tab
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { background-color: #f8f9fa; border: none; }"
        )
        layout.addWidget(scroll)
        
        # Create container widget
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # Create image label
        self.debug_image = QLabel("No debug image available")
        self.debug_image.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.debug_image.setStyleSheet(
            "QLabel { color: #6c757d; padding: 20px; }"
        )
        container_layout.addWidget(self.debug_image)
        container_layout.addStretch()
        
        scroll.setWidget(container)
        
        # Add tab
        self.addTab(tab, "Debug View")
        
    def clear(self):
        """Clear all results."""
        self.current_results = None
        self.vision_text.clear()
        self.vision_text.setPlaceholderText("No image processed yet")
        self.text_area.clear()
        self.text_area.setPlaceholderText("No text extracted yet")
        self.movie_text.clear() 
        self.movie_text.setPlaceholderText("No movie data found")
        self.debug_image.setText("No debug image available")
        self.debug_image.setPixmap(QPixmap())
        
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
            if "debug_info" in results:
                debug_info = results["debug_info"]
                text = []
                text.append("📊 Vision Analysis")
                text.append("-" * 20)
                text.append(f"🌄 Original Image: {debug_info['original_image']}")
                
                # Add confidence scores
                text.append("\n🎯 Confidence Scores:")
                for field, score in debug_info["confidence_scores"].items():
                    text.append(f"- {field}: {score:.1f}%")
                
                # Add any errors
                if "errors" in debug_info:
                    text.append("\n⚠️ Issues:")
                    for field, error in debug_info["errors"].items():
                        text.append(f"- {field}: {error}")
                
                text.append(f"\n⏱️ Timestamp: {debug_info['timestamp']}")
                self.vision_text.setPlainText("\n".join(text))
            else:
                self.vision_text.setPlainText("❌ No debug info available")
            
            # Update extracted text
            if "extracted_data" in results:
                text = []
                text.append("📚 Extracted Text")
                text.append("-" * 20)
                
                # Display title
                if results["extracted_data"]["title"]:
                    text.append("🎬 Title:")
                    text.append(results["extracted_data"]["title"])
                    
                # Display year
                if results["extracted_data"]["year"]:
                    text.append("\n📅 Year:")
                    text.append(results["extracted_data"]["year"])
                    
                # Display runtime
                if results["extracted_data"]["runtime"]:
                    text.append("\n⏱️ Runtime:")
                    text.append(results["extracted_data"]["runtime"])
                
                # Display cleaned titles if available
                if "extracted_titles" in results and results["extracted_titles"]:
                    text.append("\n🔍 Processed Titles:")
                    for title in results["extracted_titles"]:
                        text.append(f"- {title}")
                        
                self.text_area.setPlainText("\n".join(text))
            else:
                self.text_area.setPlainText("❌ No text extracted")
                
            # Update movie data
            movie = results.get("movie_data")
            if movie and isinstance(movie, dict):
                text = []
                text.append("🎥 Movie Information")
                text.append("-" * 20)
                
                # Basic info
                text.append(f"📌 Title: {movie['title']}")
                
                if "release_date" in movie:
                    text.append(f"📅 Year: {movie['release_date'][:4]}")
                    
                if "vote_average" in movie:
                    text.append(f"⭐ Rating: {movie['vote_average']:.1f}/10")
                    
                # Genres
                if "genres" in movie and movie["genres"]:
                    genres = [g["name"] for g in movie["genres"]]
                    text.append(f"🏷️ Genres: {', '.join(genres)}")
                    
                # Overview
                if "overview" in movie:
                    text.append("\n📝 Overview:")
                    text.append(movie['overview'])
                    
                self.movie_text.setPlainText("\n".join(text))
            else:
                self.movie_text.setPlainText("❌ No movie data found")
                
            # Update debug image
            if "debug_image" in results:
                pixmap = QPixmap(results["debug_image"])
                if not pixmap.isNull():
                    # Scale pixmap to fit while maintaining aspect ratio
                    scaled = pixmap.scaled(
                        800, 800,  # Max dimensions
                        QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                        QtCore.Qt.TransformationMode.SmoothTransformation
                    )
                    self.debug_image.setPixmap(scaled)
                    
        except Exception as e:
            self.logger.exception("Update error")
            # Set error messages in each tab
            self.vision_text.setText("Error updating vision data")
            self.text_area.setText("Error updating extracted text")
            self.movie_text.setText("Error updating movie data")
            
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
