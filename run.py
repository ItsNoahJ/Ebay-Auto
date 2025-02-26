#!/usr/bin/env python3
"""
Main launcher for the Media Processor application.
"""
import os
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version meets requirements."""
    if sys.version_info < (3, 9):
        print("Error: Python 3.9 or higher is required")
        return False
    return True

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
    print("Initializing Media Processor...")
    
    # Check Python version
    if not check_python_version():
        return 1
        
    # Create directories
    create_directories()
    
    try:
        # Import and run GUI selector
        from src.gui_selector import main as run_selector
        run_selector()
        return 0
        
    except ImportError:
        print("Error: Could not load GUI selector")
        print("Please check that PyQt6 is installed:")
        print("pip install PyQt6")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
