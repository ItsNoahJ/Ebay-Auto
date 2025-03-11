"""
Main window module.
"""
import logging
import sys
import cv2
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import pyqtSlot, QThread, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
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
from .widgets import ConnectionStatusWidget, ProcessingStatusWidget

class ProcessingThread(QThread):
    """Thread for processing images."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str, float)  # (stage_id, progress)
    
    def __init__(self, coordinator, image_path):
        super().__init__()
        self.coordinator = coordinator
        self.image_path = image_path
        self.stages = ["grayscale", "resize", "enhance", "denoise", "text"]
        
    def run(self):
        """Run processing in background thread."""
        try:
            # Initialize progress for all stages
            for stage in self.stages:
                self.progress.emit(stage, 0.0)
            
            # Load image
            image = cv2.imread(self.image_path)
            if image is None:
                raise ValueError("Failed to load image")
                
            # Start processing
            results = self.coordinator.process_tape(image)
            
            if results.get("success", False):
                # Mark all stages as complete
                for stage in self.stages:
                    self.progress.emit(stage, 1.0)
                self.finished.emit(results)
            else:
                error = results.get("error", "Unknown error occurred")
                # Reset incomplete stages
                for stage in self.stages:
                    if not results.get(f"{stage}_complete", False):
                        self.progress.emit(stage, 0.0)
                        
                # Check for timeout vs other errors
                if "timeout" in error.lower() or "timed out" in error.lower():
                    results["error_type"] = "timeout"
                else:
                    results["error_type"] = "error"
                self.finished.emit(results)
            
        except Exception as e:
            # Reset all progress on exception
            for stage in self.stages:
                self.progress.emit(stage, 0.0)
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize window."""
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self.coordinator = ProcessingCoordinator()
        self.current_image = None
        self.current_status = "disconnected"  # Start disconnected to avoid timeouts
        self.processing_complete = False
        self.logger.info(f"Initial LM Studio status: {self.current_status}")
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
        self.setWindowTitle("Automedia Suite")
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
        # Add LM Studio status
        self.lm_status = ConnectionStatusWidget()
        self.statusBar().addPermanentWidget(self.lm_status)
        
        # Add processing status
        self.processing_status = ProcessingStatusWidget()
        self.statusBar().addPermanentWidget(self.processing_status)
        
        # Connect status signals
        self.logger.info("Connecting LM Studio status signal...")
        self.lm_status.status_changed.connect(self._on_lm_status_changed)
        self.logger.info("LM Studio status signal connected")
        
    def _create_widgets(self):
        """Create widgets."""
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Create layout
        layout = QHBoxLayout(central)
        layout.setSpacing(10)  # Add space between widgets
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins around edges
        
        # Create preview widget
        self.preview = ImagePreview()
        self.preview.setMinimumWidth(GUI_SETTINGS["min_preview_width"])
        self.preview.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.preview, stretch=1)
        
        # Create results widget
        self.results = ResultsView()
        self.results.setMinimumWidth(GUI_SETTINGS["min_results_width"])
        self.results.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.results, stretch=1)
        
        # Connect signals
        self.logger.info("Setting up signal connections...")
        self.preview.image_loaded.connect(self._on_image_loaded)
        self.logger.info("Image loaded signal connected")
        
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
    def _on_processing_error(self, error: str):
        """Handle processing errors."""
        self.logger.error(f"Processing error: {error}")
        self.processing_status.finish_processing(False)
        self.lm_status.stop_loading_animation()
        self.processing_complete = True  # Mark as complete even on error
        QMessageBox.critical(self, "Error", f"Processing failed: {error}")

    def _on_image_loaded(self, image_path: str):
        """Handle loaded image."""
        self.logger.info(f"Image loaded event received. Path: {image_path}")
        self.logger.info(f"Current LM Studio status: {self.current_status}")
        
        # Update state
        self.logger.info("Updating current_image state...")
        self.current_image = image_path
        
        # Update button states
        should_enable = True  # Allow processing even if LM Studio is not connected
        self.logger.info(f"Setting process button enabled: {should_enable}")
        self.process_action.setEnabled(should_enable)
        
        self.logger.info("Setting clear button enabled")
        self.clear_action.setEnabled(True)
        
        self.logger.info(f"Final process button state: {self.process_action.isEnabled()}")
            
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
        self.results.clear()  # This will clear all results including preprocessing images
        self.process_action.setEnabled(False)
        self.clear_action.setEnabled(False)
        self.save_action.setEnabled(False)
        self.statusBar().showMessage("Ready")
        self.processing_status.reset()
        
    @pyqtSlot()
    def _process_image(self):
        """Process current image."""
        if not self.current_image:
            self.logger.warning("No image selected for processing")
            return
            
        # Allow processing even if LM Studio is not connected
        if self.current_status != "connected":
            self.logger.warning(f"Processing without LM Studio (status: {self.current_status})")
            
        self.logger.info(f"Starting processing of image: {self.current_image}")
            
        try:
            # Reset completion state
            self.processing_complete = False
            
            # Start loading animation and processing status
            self.lm_status.start_loading_animation()
            self.processing_status.start_processing()
            
            # Skip connection check
            self.logger.info("Skipping LM Studio connection check")
            
            # Create and start processing thread
            self.processing_thread = ProcessingThread(
                self.coordinator,
                self.current_image
            )
            
            def on_processing_finished(results):
                self.logger.info("Processing completed successfully")
                if "error" in results:
                    if "timeout" in results["error"].lower():
                        self.processing_status.finish_processing(
                            False, 
                            error_type="timeout",
                            error_msg=results["error"]
                        )
                    else:
                        self.processing_status.finish_processing(
                            False,
                            error_type="error",
                            error_msg=results["error"]
                        )
                else:
                    # Get preprocessing images from coordinator
                    preprocessing_images = self.coordinator.get_preprocessing_images()
                    
                    # Log available stages
                    self.logger.info(f"Available preprocessing stages: {list(preprocessing_images.keys())}")
                    
                    # Update results view with data and images
                    self.results.update_results(results)
                    
                    # Map vision processor stages to result view stages
                    stage_mapping = {
                        "Original": "Original",
                        "grayscale": "Grayscale",
                        "enhance": "Enhanced",
                        "text": "Text"
                    }
                    
                    for src_stage, dest_stage in stage_mapping.items():
                        if src_stage in preprocessing_images:
                            self.logger.info(f"Updating stage {src_stage} -> {dest_stage}")
                            self.results.update_preprocessing_image(dest_stage, preprocessing_images[src_stage])
                        
                    self.save_action.setEnabled(True)
                    self.processing_status.finish_processing(True)
                    
                    # Auto-save if enabled
                    if self.settings["general"]["auto_save"]:
                        results_dir = Path("storage/results")
                        results_dir.mkdir(parents=True, exist_ok=True)
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        json_path = results_dir / f"results_{timestamp}.json"
                        
                        self.results.save_results(str(json_path))
                        self.statusBar().showMessage(f"Auto-saved to: {json_path}")
                
                self.lm_status.stop_loading_animation()
                self.processing_complete = True
                
            def on_processing_error(error):
                self._on_processing_error(error)
                self.processing_complete = True
                
            def on_processing_progress(stage_id, progress):
                if not self.processing_complete:  # Only update if still processing
                    self.logger.debug(f"Processing progress: {stage_id} = {progress}")
                    self.processing_status.update_stage(stage_id, progress)
                
            self.processing_thread.finished.connect(on_processing_finished)
            self.processing_thread.error.connect(on_processing_error)
            self.processing_thread.progress.connect(on_processing_progress)
            self.processing_thread.start()
            
        except Exception as e:
            self.logger.exception("Processing error")
            QMessageBox.critical(
                self,
                "Error",
                f"Processing failed: {e}"
            )
            self.lm_status.stop_loading_animation()
            self.processing_status.finish_processing(False)
            
    @pyqtSlot(str)
    def _on_lm_status_changed(self, status: str):
        """Handle LM Studio status changes."""
        self.current_status = status
        self.logger.info(f"LM Studio status changed to: {status}")
        
        # Enable/disable process button based on connection and image
        can_process = status == "connected" and self.current_image is not None
        self.process_action.setEnabled(can_process)
        
        # Update status bar message
        if status == "connected":
            msg = "Ready - Connected to LM Studio"
        elif status == "no_model":
            msg = "Warning - No model loaded in LM Studio"
        else:
            msg = "Error - Not connected to LM Studio"
        self.statusBar().showMessage(msg)
        
        self.logger.info(f"Process button enabled: {can_process}")
        
    def closeEvent(self, event):
        """Handle window close."""
        event.accept()
