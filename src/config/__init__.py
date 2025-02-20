"""
Configuration package.
"""
import os
from typing import Dict, Any
from .settings import validate_settings

def initialize_config() -> Dict[str, Any]:
    """Initialize and validate configuration settings."""
    # Ensure TESSERACT_CMD is set before importing vision modules
    tesseract_path = os.getenv('TESSERACT_PATH', r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if os.path.exists(tesseract_path):
        os.environ['TESSERACT_CMD'] = tesseract_path
        os.environ['TESSDATA_PREFIX'] = os.path.join(os.path.dirname(tesseract_path), 'tessdata')
    
    return validate_settings()
