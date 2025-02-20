"""
GUI entry point module.
"""
import logging
import sys

from PyQt6.QtWidgets import QApplication

from .config.settings import validate_settings
from .gui.main_window import MainWindow

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def run():
    """Run the GUI application."""
    return main()

def main():
    """Main entry point."""
    try:
        # Setup logging
        setup_logging()
        
        # Validate settings
        validate_settings()
        
        # Create application
        app = QApplication(sys.argv)
        
        # Create main window
        window = MainWindow()
        window.show()
        
        # Run event loop
        return app.exec()
        
    except Exception as e:
        logging.exception("Application error")
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
