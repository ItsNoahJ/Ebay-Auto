"""
Main window module.
"""
import logging
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QLabel,
    QProgressBar
)

from ..config.settings import GUI_SETTINGS
from ..models.coordinator import ProcessingCoordinator
from .image_preview import ImagePreview
from .results_view import ResultsView
from .settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize window."""
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self.coordinator = ProcessingCoordinator()
        self.current_image = None
        self.settings = {
            "general": {
                "debug_enabled": True,
                "auto_save": False
            },
            "camera": {
                "enabled": False,
                "device_id": 0
            }
        }
        
        # Configure window
        self.setWindowTitle("VHS Tape Scanner")
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
        
        self.settings_action = QAction("Se&ttings...", self)
        self.settings_action.triggered.connect(self._show_settings)
        
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        
        # Process action
        self.process_action = QAction("Process", self)
        self.process_action.setShortcut("Ctrl+P")
        self.process_action.triggered.connect(self._process_image)
        self.process_action.setEnabled(False)
        
        # Clear action
        self.clear_action = QAction("Clear", self)
        self.clear_action.triggered.connect(self._clear)
        self.clear_action.setEnabled(False)
        
    def _create_menu(self):
        """Create menu bar."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addAction(self.settings_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # Edit menu
        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self.clear_action)
        
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
        toolbar.addAction(self.process_action)
        toolbar.addAction(self.clear_action)
        
    def _create_statusbar(self):
        """Create status bar."""
        self.statusBar().showMessage("Ready")
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.hide()
        self.statusBar().addPermanentWidget(self.progress_bar)
        
    def _create_widgets(self):
        """Create widgets."""
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Create layout
        layout = QHBoxLayout(central)
        
        # Create preview widget
        self.preview = ImagePreview()
        layout.addWidget(self.preview, stretch=1)
        
        # Create results widget
        results_layout = QVBoxLayout()
        self.results = ResultsView()
        results_layout.addWidget(self.results)
        layout.addLayout(results_layout, stretch=1)
        
        # Connect signals
        self.preview.image_loaded.connect(self._on_image_loaded)
        
    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.apply_settings(self.settings)
        
        if dialog.exec():
            self.settings = dialog.get_settings()
            
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
            self.preview.load_image(image_path)
            
    @pyqtSlot(str)
    def _on_image_loaded(self, image_path: str):
        """Handle loaded image."""
        self.current_image = image_path
        self.process_action.setEnabled(True)
        self.clear_action.setEnabled(True)
            
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
    def _clear(self):
        """Clear current image and results."""
        self.current_image = None
        self.preview.clear()
        self.results.clear()
        self.process_action.setEnabled(False)
        self.clear_action.setEnabled(False)
        self.save_action.setEnabled(False)
        self.statusBar().showMessage("Ready")
        
    @pyqtSlot()
    def _process_image(self):
        """Process current image."""
        if not self.current_image:
            return
            
        try:
            # Show progress
            self.progress_bar.setRange(0, 0)
            self.progress_bar.show()
            self.statusBar().showMessage("Processing...")
            
            # Process image
            results = self.coordinator.process_tape(
                self.current_image,
                debug=self.settings["general"]["debug_enabled"]
            )
            
            if results["success"]:
                # Update results view
                self.results.update_results(results)
                self.save_action.setEnabled(True)
                
                # Auto-save if enabled
                if self.settings["general"]["auto_save"]:
                    results_dir = Path("storage/results")
                    results_dir.mkdir(parents=True, exist_ok=True)
                    
                    timestamp = results["timestamp"].strftime("%Y%m%d_%H%M%S")
                    json_path = results_dir / f"vhs_data_{timestamp}.json"
                    
                    self.results.save_results(str(json_path))
                    self.statusBar().showMessage(
                        f"Results auto-saved to: {json_path}"
                    )
                else:
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
            
        finally:
            # Hide progress
            self.progress_bar.hide()
            
    def closeEvent(self, event):
        """Handle window close."""
        event.accept()
