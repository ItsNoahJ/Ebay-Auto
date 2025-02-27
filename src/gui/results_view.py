"""
Results view widget.
"""
from PyQt6.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QTabWidget

class ResultsView(QWidget):
    """Widget for displaying processing results."""
    
    def __init__(self):
        """Initialize widget."""
        super().__init__()
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Create text areas
        self.text_area = QTextEdit()
        self.movie_text = QTextEdit()
        self.audio_text = QTextEdit()
        
        self.text_area.setReadOnly(True)
        self.movie_text.setReadOnly(True)
        self.audio_text.setReadOnly(True)
        
        # Add tabs
        tabs.addTab(self.text_area, "Extracted Text")
        tabs.addTab(self.movie_text, "Movie Details")
        tabs.addTab(self.audio_text, "Audio Details")
        
    def _ensure_list(self, value) -> list:
        """Ensure value is a list."""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]
        
    def update_results(self, results):
        """
        Update displayed results.
        
        Args:
            results: Dictionary of processing results
        """
        if not results.get("success", False):
            self.text_area.setText("Error: " + results.get("error", "Unknown error"))
            self.movie_text.setText("No movie data")
            self.audio_text.setText("No audio data")
            return
            
        # Update extracted text tab
        text_content = []
        if results.get("extracted_titles"):
            text_content.append("Extracted Titles:")
            for title in results["extracted_titles"]:
                text_content.append(f"- {title}")
        else:
            text_content.append("No text extracted")
            
        if results.get("vision_data"):
            text_content.append("\nVision Processing Data:")
            for key, value in results["vision_data"].items():
                text_content.append(f"{key}: {value}")
                
        self.text_area.setText("\n".join(text_content))
        
        # Update movie tab
        movie_content = []
        if results.get("movie_data"):
            data = results["movie_data"]
            if any(data.values()):  # Check if any values are non-None
                movie_content.extend([
                    f"Title: {data.get('title', 'Unknown')}",
                    f"Year: {data.get('year', 'Unknown')}",
                    f"Runtime: {data.get('runtime', 'Unknown')} minutes",
                    "",
                    f"Director: {data.get('director', 'Unknown')}",
                    "",
                    "Cast:",
                    " ".join(self._ensure_list(data.get('cast', []))),
                    "",
                    "Genre:",
                    " ".join(self._ensure_list(data.get('genre', []))),
                    "",
                    "Plot:",
                    data.get('plot', 'No plot available') or 'No plot available'
                ])
            else:
                movie_content.append("No movie data available")
        else:
            movie_content.append("No movie data available")
            
        self.movie_text.setText("\n".join(movie_content))
        
        # Update audio tab
        audio_content = []
        if results.get("audio_data"):
            data = results["audio_data"]
            if any(data.values()):  # Check if any values are non-None
                audio_content.extend([
                    f"Artist: {data.get('artist', 'Unknown')}",
                    f"Album: {data.get('album', 'Unknown')}",
                    f"Year: {data.get('year', 'Unknown')}",
                    "",
                    f"Label: {data.get('label', 'Unknown')}",
                    f"Format: {data.get('format', 'Unknown')}",
                    "",
                    "Genre:",
                    " ".join(self._ensure_list(data.get('genre', []))),
                    "",
                    "Tracks:",
                    "\n".join(self._ensure_list(data.get('tracks', [])))
                ])
            else:
                audio_content.append("No audio data available")
        else:
            audio_content.append("No audio data available")
            
        self.audio_text.setText("\n".join(audio_content))
