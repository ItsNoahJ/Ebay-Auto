#!/usr/bin/env python3
"""
Launch script for the PyQt GUI application.
"""
import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import PyQt6
        import cv2
        import numpy
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("\nPlease install required dependencies:")
        print("pip install -r requirements.txt")
        return False

def create_directories():
    """Create necessary directories."""
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
        
    # Create directories
    create_directories()
    print("Setup checks passed!")
    
    # Start the application
    print("\nStarting VHS Tape Scanner with PyQt interface...")
    
    try:
        # Set QT_AUTO_SCREEN_SCALE_FACTOR for high DPI support
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        
        from src.main_gui import main
        main()
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
