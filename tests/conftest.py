"""
Test configuration and shared fixtures.
"""
import pytest
import numpy as np
from unittest.mock import Mock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap

@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture
def qtbot(qapp):
    """Create QtBot instance if pytest-qt is available."""
    try:
        from pytestqt.qt_compat import qt_api
        return qt_api.QtBot(qapp)
    except ImportError:
        # Return a minimal mock for non-GUI tests
        class MinimalQtBot:
            def addWidget(self, _): pass
            def mouseClick(self, *args, **kwargs): pass
            def keyClicks(self, *args, **kwargs): pass
            def waitActive(self, _): pass
            def waitExposed(self, _): pass
            def wait(self, _): pass
        return MinimalQtBot()
    
@pytest.fixture
def mock_vision():
    """Create mock vision instance."""
    mock = Mock()
    mock.check_models = Mock(return_value=True)
    mock.available_models = ["model1", "model2"]
    mock.extract_text = Mock(return_value={
        "success": True,
        "text": "Sample text",
        "confidence": 0.9
    })
    return mock

@pytest.fixture
def test_results():
    """Create test OCR results."""
    return {
        "success": True,
        "vision_data": {
            "title": "Test Title",
            "year": "2025",
            "runtime": "120 min",
            "confidence": {
                "title": 0.95,
                "year": 0.85,
                "runtime": 0.75
            }
        }
    }

@pytest.fixture
def invalid_results():
    """Create test invalid results."""
    return {
        "success": False,
        "error": "Test error message"
    }

@pytest.fixture
def mock_qimage():
    """Create mock QImage."""
    mock = Mock()
    mock.scaled = Mock(return_value=mock)
    mock.size = Mock(return_value=(100, 100))
    return mock

@pytest.fixture
def mock_qpixmap():
    """Create mock QPixmap."""
    mock = Mock()
    mock.scaled = Mock(return_value=mock)
    mock.size = Mock(return_value=(100, 100))
    mock.isNull = Mock(return_value=False)
    mock.width = Mock(return_value=100)
    mock.height = Mock(return_value=100)
    return mock

@pytest.fixture
def mock_preprocessed_image():
    """Create mock preprocessed image as numpy array."""
    return np.zeros((100, 100, 3), dtype=np.uint8)
