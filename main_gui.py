#!/usr/bin/env python
"""
GUI application entry point.
"""
import sys
import os
import logging
from pathlib import Path

def setup_environment():
    """Setup application environment."""
    try:
        # Add src directory to path
        src_dir = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_dir))
        
        # Create assets directory
        assets_dir = Path(__file__).parent / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        # Create storage directory
        storage_dir = Path(__file__).parent / "storage"
        storage_dir.mkdir(exist_ok=True)
        
        # Setup logging
        level = os.getenv("LOG_LEVEL", "INFO")
        log_file = os.getenv("LOG_FILE")
        
        config = {
            "level": level,
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
        
        if log_file:
            config["filename"] = log_file
            
        logging.basicConfig(**config)
        
    except Exception as e:
        print(f"Failed to setup environment: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    # Setup environment
    setup_environment()
    
    try:
        # Import GUI after environment setup
        from src.gui.app import Application
        
        # Create and run application
        app = Application()
        return app.run()
        
    except ImportError as e:
        print(f"Failed to import GUI components: {e}")
        print("Make sure PyQt5 is installed:")
        print("pip install PyQt5")
        return 1
        
    except Exception as e:
        print(f"Application error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
