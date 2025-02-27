"""
Custom widgets for the GUI.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QPushButton
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
import requests

class ConnectionStatusWidget(QWidget):
    """Widget showing LM Studio connection status."""
    
    status_changed = pyqtSignal(str)  # Emits status changes
    
    def __init__(self, parent=None):
        """Initialize widget."""
        super().__init__(parent)
        
        # Create container frame
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container {
                background-color: transparent;
                border-radius: 8px;
                padding: 2px;
            }
        """)
        
        # Create layout
        layout = QHBoxLayout(self.container)
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
        
        # Create refresh button
        self.refresh_button = QPushButton("↻")  # Unicode refresh symbol
        self.refresh_button.setFixedSize(20, 20)
        self.refresh_button.setToolTip("Check LM Studio connection")
        self.refresh_button.clicked.connect(self.check_connection)
        layout.addWidget(self.refresh_button)
        
        # Setup main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        
        # Create pulse animation
        self.pulse_animation = QPropertyAnimation(self.container, b"styleSheet")
        self.pulse_animation.setDuration(1000)  # 1 second per pulse
        self.pulse_animation.setLoopCount(-1)  # Loop indefinitely
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Initialize state
        self.model_loaded = False
        
        # Initial check (full check including model)
        self.check_connection(check_model=True)
        
    def check_connection(self, check_model=False):
        """Check LM Studio connection status."""
        try:
            # Try to connect to LM Studio (quick ping)
            response = requests.get("http://127.0.0.1:1234/v1/models", timeout=2)
            
            if response.status_code == 200:
                # If this is startup or we need to check model status
                if check_model:
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
                            self.model_loaded = True
                            self._update_status("connected")
                        else:
                            self.model_loaded = False
                            self._update_status("no_model")
                    except requests.RequestException:
                        self.model_loaded = False
                        self._update_status("no_model")
                else:
                    # For manual refresh, use cached model state
                    self._update_status("connected" if self.model_loaded else "no_model")
            else:
                self.model_loaded = False
                self._update_status("disconnected")
                
        except requests.RequestException:
            self.model_loaded = False
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
        
    def start_loading_animation(self):
        """Start the pulsing blue animation."""
        self.pulse_animation.setStartValue("""
            QFrame#container {
                background-color: transparent;
                border-radius: 8px;
                padding: 2px;
            }
        """)
        self.pulse_animation.setEndValue("""
            QFrame#container {
                background-color: rgba(0, 120, 255, 0.3);
                border-radius: 8px;
                padding: 2px;
            }
        """)
        self.pulse_animation.start()
        
    def stop_loading_animation(self):
        """Stop the pulsing animation."""
        self.pulse_animation.stop()
        self.container.setStyleSheet("""
            QFrame#container {
                background-color: transparent;
                border-radius: 8px;
                padding: 2px;
            }
        """)
