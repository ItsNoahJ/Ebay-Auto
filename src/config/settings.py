"""
Configuration settings module.
"""
import os
from pathlib import Path
from typing import Dict, Union

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"

# Storage paths
STORAGE_PATHS = {
    "cache": STORAGE_DIR / "cache",
    "images": STORAGE_DIR / "images",
    "results": STORAGE_DIR / "results",
    "debug": STORAGE_DIR / "debug",
}

# Vision settings
VISION_SETTINGS = {
    # Tesseract configuration
    "tesseract_cmd": os.getenv("TESSERACT_CMD"),
    "tesseract_config": "--psm 11",  # Page segmentation mode
    
    # Image preprocessing
    "target_width": int(os.getenv("VISION_TARGET_WIDTH", "1920")),
    "min_cover_area": int(os.getenv("VISION_MIN_COVER_AREA", "10000")),
    "max_cover_area_ratio": float(os.getenv("VISION_MAX_COVER_RATIO", "0.8")),
    "epsilon_factor": float(os.getenv("VISION_EPSILON_FACTOR", "0.02")),
    
    # Text detection
    "text_block_size": 11,  # Must be odd
    "text_c": 9,  # Lower = more aggressive
}

# Camera settings
CAMERA_SETTINGS = {
    "device_id": int(os.getenv("CAMERA_DEVICE_ID", "0")),
    "resolution_width": 1920,
    "resolution_height": 1080,
    "auto_focus": True,
    "focus_value": None,  # 0-255, None for auto
    "auto_exposure": True,
    "exposure_value": None,  # Platform dependent
}

# GUI settings
GUI_SETTINGS = {
    "window_width": int(os.getenv("GUI_WINDOW_WIDTH", "1280")),
    "window_height": int(os.getenv("GUI_WINDOW_HEIGHT", "720")),
    "preview_fps": 30,
    "preview_scale": 0.5,  # Scale preview to 50%
    "theme": os.getenv("GUI_THEME", "light"),
}

# API settings
API_SETTINGS = {
    "tmdb_api_key": os.getenv("TMDB_API_KEY"),
    "timeout": int(os.getenv("API_TIMEOUT", "10")),
    "max_retries": int(os.getenv("API_MAX_RETRIES", "3")),
    "rate_limit": int(os.getenv("API_RATE_LIMIT", "40")),  # Requests per window
    "rate_window": int(os.getenv("API_RATE_WINDOW", "10")),  # Window in seconds
    "cache_ttl": int(os.getenv("API_CACHE_TTL", "86400")),  # 24 hours
}

def validate_settings():
    """Validate required settings."""
    # Check Tesseract
    if not VISION_SETTINGS["tesseract_cmd"]:
        raise ValueError("TESSERACT_CMD not configured")
        
    # Check TMDb API key
    if not API_SETTINGS["tmdb_api_key"]:
        raise ValueError("TMDB_API_KEY not configured")
        
    # Create storage directories
    for path in STORAGE_PATHS.values():
        path.mkdir(parents=True, exist_ok=True)
