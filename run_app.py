#!/usr/bin/env python3
"""
Quick start script for the Media Processor application.
"""
import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import flet
        import cv2
        import numpy
        import pytesseract
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("\nPlease install required dependencies:")
        print("pip install -r requirements.txt")
        return False

def check_tesseract():
    """Check if Tesseract OCR is installed and configured."""
    try:
        import pytesseract
        # Set Tesseract path from environment variable
        tesseract_path = os.getenv('TESSERACT_PATH', r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            os.environ['TESSDATA_PREFIX'] = os.path.join(os.path.dirname(tesseract_path), 'tessdata')
        pytesseract.get_tesseract_version()
        return True
    except Exception as e:
        print("\nTesseract OCR is not properly configured.")
        print(f"Error: {e}")
        print("Please install Tesseract OCR:")
        print("- Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("- Linux: sudo apt-get install tesseract-ocr")
        print("- macOS: brew install tesseract")
        return False

def create_test_directories():
    """Create necessary directories for testing."""
    dirs = [
        "storage/images",
        "storage/results",
        "storage/cache",
        "storage/debug"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def main():
    """Main entry point."""
    print("Checking setup...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("Error: Python 3.9 or higher is required")
        return 1
        
    # Check dependencies
    if not check_dependencies():
        return 1
        
    # Check Tesseract
    if not check_tesseract():
        return 1
        
    # Create directories
    create_test_directories()
    print("Setup checks passed!")
    
    # Start the application
    print("\nStarting Media Processor with Flet interface...")
    
    try:
        from src.main import main
        main()
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
