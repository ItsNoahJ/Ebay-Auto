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
        self.info_area = QTextEdit()
        self.movie_text = QTextEdit()
        self.audio_text = QTextEdit()
        self.raw_text = QTextEdit()
        
        self.info_area.setReadOnly(True)
        self.movie_text.setReadOnly(True)
        self.audio_text.setReadOnly(True)
        self.raw_text.setReadOnly(True)
        
        # Add tabs
        tabs.addTab(self.info_area, "Extracted Info")
        tabs.addTab(self.movie_text, "Movie Details")
        tabs.addTab(self.audio_text, "Audio Details")
        tabs.addTab(self.raw_text, "Raw Data")
        
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
            self.info_area.setText("Error: " + results.get("error", "Unknown error"))
            self.raw_text.setText("Error: " + results.get("error", "Unknown error"))
            self.movie_text.setText("No movie data")
            self.audio_text.setText("No audio data")
            return
            
        # Update extracted info tab (clean presentation)
        info_content = []
        if results.get("vision_data"):
            data = results["vision_data"]
            # Extract the actual values from the responses
            title = data.get("title", "").strip('."')  # Remove quotes and periods
            if "movie title on the VHS cover is" in title:
                title = title.split("is")[-1].strip('." ')
            
            year = data.get("year", "")
            if isinstance(year, str) and year.isdigit():
                year = year
                
            runtime = data.get("runtime", "")
            if "runtime of the movie is" in runtime:
                runtime = runtime.split("is")[-1].strip()
                
            # Add formatted information
            info_content.extend([
                "Media Information",
                "================",
                f"Title: {title}",
                f"Year: {year}",
                f"Runtime: {runtime}",
                "",
                "Confidence Scores",
                "================",
            ])
            
            if "confidence" in results.get("vision_data", {}):
                conf_data = results["vision_data"]["confidence"]
                for key, value in conf_data.items():
                    info_content.append(f"{key.capitalize()}: {value}%")
                    
        else:
            info_content.append("No information extracted")
            
        self.info_area.setText("\n".join(info_content))
        
        # Update raw data tab
        raw_content = []
        if results.get("extracted_titles"):
            raw_content.append("Extracted Titles:")
            for title in results["extracted_titles"]:
                raw_content.append(f"- {title}")
        else:
            raw_content.append("No text extracted")
            
        if results.get("vision_data"):
            raw_content.append("\nVision Processing Data:")
            for key, value in results["vision_data"].items():
                raw_content.append(f"{key}: {value}")
                
        self.raw_text.setText("\n".join(raw_content))
        
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
