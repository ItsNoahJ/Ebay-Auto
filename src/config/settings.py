"""
Configuration settings for the Media Processor application.
"""
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

def validate_settings() -> Dict[str, Any]:
    """Validate all settings and return a dict of validated settings."""
    settings = {}
    
    # Validate paths
    settings['BASE_DIR'] = BASE_DIR
    settings['STORAGE_DIR'] = STORAGE_DIR
    settings['CACHE_DIR'] = CACHE_DIR
    settings['RESULTS_DIR'] = RESULTS_DIR
    settings['DEBUG_DIR'] = DEBUG_DIR
    
    # Validate Tesseract (make it optional)
    tesseract_path = os.environ.get('TESSERACT_PATH', TESSERACT_PATH)
    if os.path.exists(tesseract_path):
        settings['TESSERACT_PATH'] = tesseract_path
    else:
        settings['TESSERACT_PATH'] = None
    
    # Validate API keys (both are optional)
    settings['TMDB_API_KEY'] = TMDB_API_KEY
    settings['DISCOGS_CONSUMER_KEY'] = DISCOGS_CONSUMER_KEY
    settings['DISCOGS_CONSUMER_SECRET'] = DISCOGS_CONSUMER_SECRET
    
    # Add other settings
    settings['GUI_SETTINGS'] = GUI_SETTINGS
    settings['CACHE_ENABLED'] = CACHE_ENABLED
    settings['CACHE_EXPIRE_AFTER'] = CACHE_EXPIRE_AFTER
    settings['OCR_CONFIDENCE_THRESHOLD'] = OCR_CONFIDENCE_THRESHOLD
    settings['MAX_IMAGE_SIZE'] = MAX_IMAGE_SIZE
    settings['DEBUG'] = DEBUG
    settings['SAVE_DEBUG_IMAGES'] = SAVE_DEBUG_IMAGES
    
    return settings

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
CACHE_DIR = STORAGE_DIR / "cache"
RESULTS_DIR = STORAGE_DIR / "results"
DEBUG_DIR = STORAGE_DIR / "debug"

# Storage paths configuration
STORAGE_PATHS = {
    'base': BASE_DIR,
    'storage': STORAGE_DIR,
    'cache': CACHE_DIR,
    'results': RESULTS_DIR,
    'debug': DEBUG_DIR,
    'images': STORAGE_DIR / "images",
    'temp': STORAGE_DIR / "temp"
}

# Ensure directories exist
for directory in STORAGE_PATHS.values():
    directory.mkdir(parents=True, exist_ok=True)

# Import required modules
import sys
import pytesseract

# Tesseract Configuration
TESSERACT_PATH = os.getenv('TESSERACT_PATH', r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# Ensure tesseract directory is in PATH
tesseract_dir = os.path.dirname(TESSERACT_PATH)
if tesseract_dir not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + tesseract_dir

# Configure tesseract path
if os.path.exists(TESSERACT_PATH):
    os.environ['TESSERACT_CMD'] = TESSERACT_PATH
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# GUI Settings
GUI_SETTINGS = {
    "window_title": "VHS Scanner",  # Window title
    "window_width": 1200,          # Default window width
    "window_height": 800,          # Default window height
    "preview_scale": 0.5,          # Scale factor for preview images
    "max_preview_width": 800,      # Maximum width for preview images
    "max_preview_height": 600,     # Maximum height for preview images
    "min_preview_width": 400,      # Minimum width for preview panel
    "min_results_width": 400,      # Minimum width for results panel
    "spacing": 10,                 # Layout spacing
    "margin": 10,                  # Layout margin
    "theme": "dark",               # Default theme (dark/light)
    "themes": {
        "dark": {
            "background": "#2b2b2b",
            "foreground": "#ffffff",
            "accent": "#007acc"
        },
        "light": {
            "background": "#ffffff",
            "foreground": "#000000",
            "accent": "#0066b3"
        }
    }
}

# Vision Processing Settings
VISION_SETTINGS = {
    "min_confidence": 50,  # Lowered minimum confidence threshold
    "preprocessing": {
        "denoise": True,
        "contrast": True,
        "threshold": True,
        "deskew": True
    },
    "text_extraction": {
        "lang": "eng",  # Default OCR language
        "psm": 3,  # Auto-detect page segmentation mode
        "oem": 3   # LSTM only - more accurate
    },
    # Tesseract configuration optimized for VHS cover text with custom page segmentation
    "tesseract_config": "--psm 4 --oem 1 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -c textord_min_linesize=2.5",
    "tesseract_cmd": TESSERACT_PATH,  # Path to Tesseract executable
    "enhance_contrast": True,  # Enable contrast enhancement
    "sharpen": True,  # Enable image sharpening
    "denoise": True  # Enable denoising
}

# API Configuration (all optional)
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
DISCOGS_CONSUMER_KEY = os.getenv('DISCOGS_CONSUMER_KEY', '')
DISCOGS_CONSUMER_SECRET = os.getenv('DISCOGS_CONSUMER_SECRET', '')

# Cache Settings
CACHE_ENABLED = True
CACHE_EXPIRE_AFTER = 3600  # 1 hour

# Processing Settings
OCR_CONFIDENCE_THRESHOLD = 60  # Minimum confidence score for OCR results
MAX_IMAGE_SIZE = 4000  # Maximum dimension for processed images

# Camera Settings
CAMERA_SETTINGS = {
    "device_id": 0,          # Default camera device
    "frame_width": 1280,     # HD resolution width
    "frame_height": 720,     # HD resolution height
    "fps": 30,              # Frame rate
    "auto_focus": True,      # Enable auto focus
    "exposure": -3,          # Slightly darker for better text contrast
    "brightness": 100,       # Default brightness
    "contrast": 100         # Default contrast
}

# Debug Settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SAVE_DEBUG_IMAGES = DEBUG
