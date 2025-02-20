#!/usr/bin/env python3
"""
Runner script that ensures proper Python path setup.
"""
import os
import sys
from pathlib import Path

def setup_environment():
    """Setup the Python path and environment."""
    # Add src directory to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path.absolute()))
    
    # Set environment variables if not already set
    if not os.environ.get("TESSERACT_PATH"):
        os.environ["TESSERACT_PATH"] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if __name__ == "__main__":
    setup_environment()
    
    # Import and run the app
    from flet_gui.app import main
    main()
