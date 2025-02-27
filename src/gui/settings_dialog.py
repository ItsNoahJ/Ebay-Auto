"""
Settings dialog module.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSpinBox,
    QCheckBox,
    QGroupBox,
    QLineEdit,
    QMessageBox
)
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from .camera_preview import CameraPreview
from ..config.settings import GUI_SETTINGS
from ..utils.env_utils import (
    get_api_keys, set_api_key,
    test_tmdb_api_key, test_discogs_keys
)

class SettingsDialog(QDialog):
    """Settings dialog."""
    
    def __init__(self, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        
        self.setWindowTitle("Settings")
        self.resize(600, 400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Create tabs
        self.general_tab = GeneralSettingsTab()
        tabs.addTab(self.general_tab, "General")
        
        self.api_tab = APISettingsTab()
        tabs.addTab(self.api_tab, "API Settings")
        
        self.camera_tab = CameraSettingsTab()
        tabs.addTab(self.camera_tab, "Beta: Live Camera")
        
        # Create button box
        button_box = QHBoxLayout()
        layout.addLayout(button_box)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        button_box.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(cancel_button)

    def get_settings(self):
        """Get current settings."""
        return {
            "general": self.general_tab.get_settings(),
            "camera": self.camera_tab.get_settings(),
            "api": self.api_tab.get_settings()
        }
        
    def apply_settings(self, settings):
        """Apply settings."""
        if "general" in settings:
            self.general_tab.apply_settings(settings["general"])
        if "camera" in settings:
            self.camera_tab.apply_settings(settings["camera"])
        if "api" in settings:
            self.api_tab.apply_settings(settings["api"])
            
    def accept(self):
        """Handle dialog acceptance."""
        # Save API keys first
        self.api_tab.save_api_keys()
        super().accept()

class GeneralSettingsTab(QWidget):
    """General settings tab."""
    
    def __init__(self):
        """Initialize tab."""
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        # Processing group
        processing_group = QGroupBox("Processing")
        layout.addWidget(processing_group)
        
        processing_layout = QVBoxLayout(processing_group)
        
        self.debug_checkbox = QCheckBox("Enable debug visualization")
        processing_layout.addWidget(self.debug_checkbox)
        
        self.auto_save = QCheckBox("Auto-save results")
        processing_layout.addWidget(self.auto_save)
        
        # Add stretch to bottom
        layout.addStretch()
        
    def get_settings(self):
        """Get current settings."""
        return {
            "debug_enabled": self.debug_checkbox.isChecked(),
            "auto_save": self.auto_save.isChecked()
        }
        
    def apply_settings(self, settings):
        """Apply settings."""
        if "debug_enabled" in settings:
            self.debug_checkbox.setChecked(settings["debug_enabled"])
        if "auto_save" in settings:
            self.auto_save.setChecked(settings["auto_save"])

class APISettingsTab(QWidget):
    """API settings tab."""
    
    def __init__(self):
        """Initialize tab."""
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        # TMDB group
        tmdb_group = QGroupBox("TMDB (Movie Database)")
        layout.addWidget(tmdb_group)
        
        tmdb_layout = QVBoxLayout(tmdb_group)
        
        # Add help text with link
        tmdb_help = QLabel(
            'Get a TMDB API key from: '
            '<a href="https://www.themoviedb.org/settings/api">'
            'www.themoviedb.org/settings/api</a>'
        )
        tmdb_help.setOpenExternalLinks(True)
        tmdb_layout.addWidget(tmdb_help)
        
        # API key input
        tmdb_key_layout = QHBoxLayout()
        tmdb_layout.addLayout(tmdb_key_layout)
        
        tmdb_key_layout.addWidget(QLabel("API Key:"))
        self.tmdb_key = QLineEdit()
        self.tmdb_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.tmdb_key.setPlaceholderText("Enter TMDB API key (optional)")
        tmdb_key_layout.addWidget(self.tmdb_key)
        
        self.tmdb_show = QPushButton("👁")
        self.tmdb_show.setFixedWidth(30)
        self.tmdb_show.setCheckable(True)
        self.tmdb_show.toggled.connect(
            lambda checked: self.tmdb_key.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        tmdb_key_layout.addWidget(self.tmdb_show)
        
        self.tmdb_test = QPushButton("Test Key")
        self.tmdb_test.clicked.connect(self._test_tmdb)
        tmdb_key_layout.addWidget(self.tmdb_test)
        
        # Discogs group
        discogs_group = QGroupBox("Discogs (Music Database)")
        layout.addWidget(discogs_group)
        
        discogs_layout = QVBoxLayout(discogs_group)
        
        # Add help text with link
        discogs_help = QLabel(
            'Get Discogs API keys:\n'
            '1. Create an application at '
            '<a href="https://www.discogs.com/settings/developers">'
            'www.discogs.com/settings/developers</a>\n'
            '2. Use the generated Consumer Key and Secret below'
        )
        discogs_help.setOpenExternalLinks(True)
        discogs_layout.addWidget(discogs_help)
        
        # Consumer Key input
        consumer_key_layout = QHBoxLayout()
        discogs_layout.addLayout(consumer_key_layout)
        
        consumer_key_layout.addWidget(QLabel("Consumer Key:"))
        self.discogs_key = QLineEdit()
        self.discogs_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.discogs_key.setPlaceholderText("Enter Discogs Consumer Key (optional)")
        consumer_key_layout.addWidget(self.discogs_key)
        
        self.discogs_key_show = QPushButton("👁")
        self.discogs_key_show.setFixedWidth(30)
        self.discogs_key_show.setCheckable(True)
        self.discogs_key_show.toggled.connect(
            lambda checked: self.discogs_key.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        consumer_key_layout.addWidget(self.discogs_key_show)
        
        # Consumer Secret input
        consumer_secret_layout = QHBoxLayout()
        discogs_layout.addLayout(consumer_secret_layout)
        
        consumer_secret_layout.addWidget(QLabel("Consumer Secret:"))
        self.discogs_secret = QLineEdit()
        self.discogs_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.discogs_secret.setPlaceholderText("Enter Discogs Consumer Secret (optional)")
        consumer_secret_layout.addWidget(self.discogs_secret)
        
        self.discogs_secret_show = QPushButton("👁")
        self.discogs_secret_show.setFixedWidth(30)
        self.discogs_secret_show.setCheckable(True)
        self.discogs_secret_show.toggled.connect(
            lambda checked: self.discogs_secret.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        consumer_secret_layout.addWidget(self.discogs_secret_show)
        
        # Test button
        test_layout = QHBoxLayout()
        discogs_layout.addLayout(test_layout)
        test_layout.addStretch()
        
        self.discogs_test = QPushButton("Test Keys")
        self.discogs_test.clicked.connect(self._test_discogs)
        test_layout.addWidget(self.discogs_test)
        
        # Load current keys
        self._load_current_keys()
        
        # Add stretch to bottom
        layout.addStretch()
        
    def _load_current_keys(self):
        """Load current API keys."""
        keys = get_api_keys()
        if keys["TMDB_API_KEY"]:
            self.tmdb_key.setText(keys["TMDB_API_KEY"])
        if keys["DISCOGS_CONSUMER_KEY"]:
            self.discogs_key.setText(keys["DISCOGS_CONSUMER_KEY"])
        if keys["DISCOGS_CONSUMER_SECRET"]:
            self.discogs_secret.setText(keys["DISCOGS_CONSUMER_SECRET"])
            
    def save_api_keys(self):
        """Save API keys to environment."""
        # TMDB
        tmdb_key = self.tmdb_key.text().strip()
        if tmdb_key:
            set_api_key("TMDB_API_KEY", tmdb_key)
        
        # Discogs
        discogs_key = self.discogs_key.text().strip()
        if discogs_key:
            set_api_key("DISCOGS_CONSUMER_KEY", discogs_key)
            
        discogs_secret = self.discogs_secret.text().strip()
        if discogs_secret:
            set_api_key("DISCOGS_CONSUMER_SECRET", discogs_secret)
            
    def _test_tmdb(self):
        """Test TMDB API key."""
        key = self.tmdb_key.text().strip()
        if not key:
            QMessageBox.warning(
                self,
                "Test Failed",
                "Please enter a TMDB API key first."
            )
            return
            
        if test_tmdb_api_key(key):
            QMessageBox.information(
                self,
                "Test Successful",
                "TMDB API key is valid!"
            )
        else:
            QMessageBox.warning(
                self,
                "Test Failed",
                "Invalid TMDB API key. Please check and try again."
            )
            
    def _test_discogs(self):
        """Test Discogs API keys."""
        key = self.discogs_key.text().strip()
        secret = self.discogs_secret.text().strip()
        
        if not (key and secret):
            QMessageBox.warning(
                self,
                "Test Failed",
                "Please enter both Discogs Consumer Key and Secret first."
            )
            return
            
        if test_discogs_keys(key, secret):
            QMessageBox.information(
                self,
                "Test Successful",
                "Discogs keys are valid!"
            )
        else:
            QMessageBox.warning(
                self,
                "Test Failed",
                "Invalid Discogs keys. Please check and try again."
            )
            
    def get_settings(self):
        """Get current API settings."""
        return {}  # API keys are handled separately
        
    def apply_settings(self, settings):
        """Apply API settings."""
        pass  # API keys are loaded directly from environment
        
class CameraSettingsTab(QWidget):
    """Camera settings tab."""
    
    def __init__(self):
        """Initialize tab."""
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        # Add beta warning
        warning = QLabel(
            "⚠️ Camera integration is in beta.\n"
            "Some features may be unstable."
        )
        warning.setStyleSheet("color: #f0ad4e;")
        layout.addWidget(warning)
        
        # Device group
        device_group = QGroupBox("Camera Device")
        layout.addWidget(device_group)
        
        device_layout = QVBoxLayout(device_group)
        
        self.enable_camera = QCheckBox("Enable camera integration")
        device_layout.addWidget(self.enable_camera)
        
        device_id_layout = QHBoxLayout()
        device_layout.addLayout(device_id_layout)
        
        device_id_layout.addWidget(QLabel("Device ID:"))
        self.device_id = QSpinBox()
        self.device_id.setRange(0, 10)
        device_id_layout.addWidget(self.device_id)
        device_id_layout.addStretch()
        
        # Preview group
        self.preview_group = QGroupBox("Preview")
        layout.addWidget(self.preview_group)
        
        preview_layout = QVBoxLayout(self.preview_group)
        
        self.preview = CameraPreview()
        preview_layout.addWidget(self.preview)
        
        preview_buttons = QHBoxLayout()
        preview_layout.addLayout(preview_buttons)
        
        self.start_preview = QPushButton("Start Preview")
        self.start_preview.clicked.connect(self._start_preview)
        preview_buttons.addWidget(self.start_preview)
        
        self.stop_preview = QPushButton("Stop Preview")
        self.stop_preview.clicked.connect(self._stop_preview)
        self.stop_preview.setEnabled(False)
        preview_buttons.addWidget(self.stop_preview)
        
        # Enable/disable handling
        self.enable_camera.toggled.connect(self._on_enable_toggled)
        self._on_enable_toggled(False)
        
        # Add stretch to bottom
        layout.addStretch()
        
    def get_settings(self):
        """Get current settings."""
        return {
            "enabled": self.enable_camera.isChecked(),
            "device_id": self.device_id.value()
        }
        
    def apply_settings(self, settings):
        """Apply settings."""
        if "enabled" in settings:
            self.enable_camera.setChecked(settings["enabled"])
        if "device_id" in settings:
            self.device_id.setValue(settings["device_id"])
            
    def _on_enable_toggled(self, enabled):
        """Handle enable checkbox toggle."""
        self.device_id.setEnabled(enabled)
        self.preview_group.setEnabled(enabled)
        
    def _start_preview(self):
        """Start camera preview."""
        if self.preview.start_preview(self.device_id.value()):
            self.start_preview.setEnabled(False)
            self.stop_preview.setEnabled(True)
        
    def _stop_preview(self):
        """Stop camera preview."""
        self.preview.stop_preview()
        self.start_preview.setEnabled(True)
        self.stop_preview.setEnabled(False)
        
    def closeEvent(self, event):
        """Handle dialog close."""
        self._stop_preview()
        super().closeEvent(event)
