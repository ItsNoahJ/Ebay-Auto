"""
PyTest configuration file.
"""
import os
import pytest
from pathlib import Path
import requests
from src.config.settings import STORAGE_PATHS

# Set mock environment variables for testing
os.environ["TESSERACT_CMD"] = "mock_tesseract"
os.environ["TMDB_API_KEY"] = "mock_tmdb_key"

@pytest.fixture(autouse=True, scope="session")
def setup_test_storage():
    """Create test storage directories."""
    for path in STORAGE_PATHS.values():
        path.mkdir(parents=True, exist_ok=True)
    yield
    # Could optionally clean up test directories here if needed

@pytest.fixture
def requires_lmstudio(request):
    """Check if LM Studio is running before running tests that require it."""
    try:
        response = requests.get("http://127.0.0.1:1234/v1/models")
        if response.status_code != 200:
            pytest.skip("LM Studio is not responding correctly")
    except requests.exceptions.ConnectionError:
        pytest.skip("LM Studio is not running")
    return True

def pytest_configure(config):
    """Add LM Studio marker."""
    config.addinivalue_line(
        "markers",
        "requires_lmstudio: mark test as requiring LM Studio to be running"
    )

def pytest_collection_modifyitems(config, items):
    """Handle LM Studio marker."""
    for item in items:
        if "requires_lmstudio" in item.keywords:
            item.fixturenames.append("requires_lmstudio")
