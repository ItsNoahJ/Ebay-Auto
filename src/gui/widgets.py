"""
Custom widgets for the GUI.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
import requests

class ConnectionStatusWidget(QWidget):
    """Widget showing LM Studio connection status."""
    
    status_changed = pyqtSignal(str)  # Emits status changes
    
    def __init__(self, parent=None):
        """Initialize widget."""
        super().__init__(parent)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        # Create indicator
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(12, 12)
        self.status_indicator.setStyleSheet(
            "QLabel { border-radius: 6px; background-color: red; }"
        )
        layout.addWidget(self.status_indicator)
        
        # Create label
        self.status_label = QLabel("LM Studio: Disconnected")
        layout.addWidget(self.status_label)
        
        # Start update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_connection)
        self.timer.start(5000)  # Check every 5 seconds
        
        # Initial check
        self.check_connection()
        
    def check_connection(self):
        """Check LM Studio connection status."""
        try:
            # Try to connect to LM Studio
            response = requests.get("http://127.0.0.1:1234/v1/models", timeout=2)
            
            if response.status_code == 200:
                # Check if model is loaded by attempting a simple completion
                try:
                    test_response = requests.post(
                        "http://127.0.0.1:1234/v1/chat/completions",
                        json={
                            "model": "lmstudio-community/minicpm-o-2_6",
                            "messages": [{"role": "user", "content": "test"}],
                            "max_tokens": 1
                        },
                        timeout=5
                    )
                    
                    if test_response.status_code == 200:
                        self._update_status("connected")
                    else:
                        self._update_status("no_model")
                except requests.RequestException:
                    self._update_status("no_model")
            else:
                self._update_status("disconnected")
                
        except requests.RequestException:
            self._update_status("disconnected")
            
    def _update_status(self, status: str):
        """Update status indicator."""
        if status == "connected":
            color = QColor(0, 255, 0)  # Green
            text = "LM Studio: Connected"
        elif status == "no_model":
            color = QColor(255, 255, 0)  # Yellow
            text = "LM Studio: No Model"
        else:
            color = QColor(255, 0, 0)  # Red
            text = "LM Studio: Disconnected"
            
        self.status_indicator.setStyleSheet(
            f"QLabel {{ border-radius: 6px; background-color: {color.name()}; }}"
        )
        self.status_label.setText(text)
        self.status_changed.emit(status)
