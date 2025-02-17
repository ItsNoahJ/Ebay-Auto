"""
Main window module.
"""
import logging
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..config.settings import GUI_SETTINGS
from ..models.coordinator import ProcessingCoordinator
from .camera_preview import CameraPreview
from .results_view import ResultsView

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize window."""
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self.coordinator = ProcessingCoordinator()
        self.current_image = None
        
        # Configure window
        self.setWindowTitle("VHS Tape Processor")
        self.resize(
            GUI_SETTINGS["window_width"],
            GUI_SETTINGS["window_height"]
        )
        
        # Create UI
        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_statusbar()
        self._create_widgets()
        
    def _create_actions(self):
        """Create actions."""
        # File actions
        self.open_action = QAction("&Open Image...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self._open_image)
        
        self.save_action = QAction("&Save Results...", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self._save_results)
        self.save_action.setEnabled(False)
        
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        
        # Camera actions
        self.start_preview_action = QAction("Start Preview", self)
        self.start_preview_action.triggered.connect(
            self._start_camera_preview
        )
        
        self.stop_preview_action = QAction("Stop Preview", self)
        self.stop_preview_action.triggered.connect(
            self._stop_camera_preview
        )
        self.stop_preview_action.setEnabled(False)
        
        self.capture_action = QAction("Capture Image", self)
        self.capture_action.setShortcut("Ctrl+Space")
        self.capture_action.triggered.connect(self._capture_image)
        self.capture_action.setEnabled(False)
        
        # Process actions
        self.process_action = QAction("Process Image", self)
        self.process_action.triggered.connect(self._process_image)
        self.process_action.setEnabled(False)
        
    def _create_menu(self):
        """Create menu bar."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # Camera menu
        camera_menu = self.menuBar().addMenu("&Camera")
        camera_menu.addAction(self.start_preview_action)
        camera_menu.addAction(self.stop_preview_action)
        camera_menu.addAction(self.capture_action)
        
        # Process menu
        process_menu = self.menuBar().addMenu("&Process")
        process_menu.addAction(self.process_action)
        
    def _create_toolbar(self):
        """Create tool bar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.start_preview_action)
        toolbar.addAction(self.stop_preview_action)
        toolbar.addAction(self.capture_action)
        toolbar.addSeparator()
        toolbar.addAction(self.process_action)
        
    def _create_statusbar(self):
        """Create status bar."""
        self.statusBar().showMessage("Ready")
        
    def _create_widgets(self):
        """Create widgets."""
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Create layout
        layout = QHBoxLayout(central)
        
        # Create preview widget
        preview_layout = QVBoxLayout()
        self.preview = CameraPreview()
        preview_layout.addWidget(self.preview)
        layout.addLayout(preview_layout)
        
        # Create results widget
        results_layout = QVBoxLayout()
        self.results = ResultsView()
        results_layout.addWidget(self.results)
        layout.addLayout(results_layout)
        
        # Connect signals
        self.preview.image_captured.connect(self._on_image_captured)
        
    @pyqtSlot()
    def _open_image(self):
        """Open image file."""
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if image_path:
            self.current_image = image_path
            self.preview.load_image(image_path)
            self.process_action.setEnabled(True)
            
    @pyqtSlot()
    def _save_results(self):
        """Save processing results."""
        file_dialog = QFileDialog()
        json_path, _ = file_dialog.getSaveFileName(
            self,
            "Save Results",
            "",
            "JSON Files (*.json)"
        )
        
        if json_path:
            try:
                self.results.save_results(json_path)
                self.statusBar().showMessage(
                    f"Results saved to: {json_path}"
                )
            except Exception as e:
                self.logger.exception("Save error")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save results: {e}"
                )
                
    @pyqtSlot()
    def _start_camera_preview(self):
        """Start camera preview."""
        if self.preview.start_preview():
            self.start_preview_action.setEnabled(False)
            self.stop_preview_action.setEnabled(True)
            self.capture_action.setEnabled(True)
            self.statusBar().showMessage("Camera preview started")
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to start camera preview"
            )
            
    @pyqtSlot()
    def _stop_camera_preview(self):
        """Stop camera preview."""
        self.preview.stop_preview()
        self.start_preview_action.setEnabled(True)
        self.stop_preview_action.setEnabled(False)
        self.capture_action.setEnabled(False)
        self.statusBar().showMessage("Camera preview stopped")
        
    @pyqtSlot()
    def _capture_image(self):
        """Capture camera image."""
        self.preview.capture_image()
        
    @pyqtSlot(str)
    def _on_image_captured(self, image_path: str):
        """Handle captured image."""
        self.current_image = image_path
        self.process_action.setEnabled(True)
        self.statusBar().showMessage(f"Image captured: {image_path}")
        
    @pyqtSlot()
    def _process_image(self):
        """Process current image."""
        if not self.current_image:
            return
            
        try:
            # Process image
            results = self.coordinator.process_tape(
                self.current_image,
                debug=True
            )
            
            if results["success"]:
                # Update results view
                self.results.update_results(results)
                self.save_action.setEnabled(True)
                self.statusBar().showMessage("Processing complete")
            else:
                raise RuntimeError(results["error"])
                
        except Exception as e:
            self.logger.exception("Processing error")
            QMessageBox.critical(
                self,
                "Error",
                f"Processing failed: {e}"
            )
            
    def closeEvent(self, event):
        """Handle window close."""
        self._stop_camera_preview()
        event.accept()
