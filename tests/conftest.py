"""
PyTest configuration file.
"""
import pytest
from pathlib import Path
from src.config.settings import STORAGE_PATHS

@pytest.fixture(autouse=True, scope="session")
def setup_test_storage():
    """Create test storage directories."""
    for path in STORAGE_PATHS.values():
        path.mkdir(parents=True, exist_ok=True)
    yield
    # Could optionally clean up test directories here if needed
