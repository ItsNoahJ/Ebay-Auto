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
    QGroupBox
)

from .camera_preview import CameraPreview
from ..config.settings import GUI_SETTINGS

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
            "camera": self.camera_tab.get_settings()
        }
        
    def apply_settings(self, settings):
        """Apply settings."""
        if "general" in settings:
            self.general_tab.apply_settings(settings["general"])
        if "camera" in settings:
            self.camera_tab.apply_settings(settings["camera"])

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
