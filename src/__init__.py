"""
VHS Tape Scanner package.
"""
from pathlib import Path

from .config.settings import validate_settings
from .models.coordinator import ProcessingCoordinator

__version__ = "0.1.0"

# Validate critical settings on import
validate_settings()

# Create storage directories
STORAGE_DIRS = [
    "images",
    "results",
    "cache"
]

for dir_name in STORAGE_DIRS:
    path = Path(__file__).parent.parent / "storage" / dir_name
    path.mkdir(parents=True, exist_ok=True)

# Export key components
__all__ = [
    "__version__",
    "ProcessingCoordinator"
]
