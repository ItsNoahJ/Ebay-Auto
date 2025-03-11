"""
Unit tests for ResultsView widget.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtGui import QPixmap
from src.gui.results_view import ResultsView

def has_pytest_qt():
    """Check if pytest-qt is available."""
    try:
        import pytestqt
        return True
    except ImportError:
        return False

@pytest.fixture
def mock_labels():
    """Create mock QLabels for each preprocessing stage."""
    return {
        stage: MagicMock(spec=QLabel, name=f"mock_label_{stage}")
        for stage in ["Original", "Grayscale", "Enhanced", "Denoised", "Text Detection"]
    }

@pytest.fixture
def results_view(qapp, mock_qpixmap, mock_labels):
    """Create ResultsView widget for testing."""
    with patch('PyQt6.QtWidgets.QLabel', side_effect=lambda *args: MagicMock(spec=QLabel)):
        widget = ResultsView()
        widget.setup_ui()
        # Inject our mock labels
        widget.stage_labels = mock_labels
        return widget

@pytest.mark.skipif(not has_pytest_qt(), reason="requires pytest-qt")
def test_confidence_visualization(results_view, test_results, qtbot):
    """Test confidence score visualization."""
    qtbot.addWidget(results_view)
    
    # Update with test results
    results_view.update_results(test_results)
    
    # Verify text display
    assert "Test Title" in results_view.text_edit.toPlainText()
    assert "2025" in results_view.text_edit.toPlainText()
    assert "120 min" in results_view.text_edit.toPlainText()
    
    # Verify confidence bars
    assert results_view.confidence_bars["title"].value() == 95
    assert results_view.confidence_bars["year"].value() == 85
    assert results_view.confidence_bars["runtime"].value() == 75

@pytest.mark.skipif(not has_pytest_qt(), reason="requires pytest-qt")
def test_preprocessing_image_display(results_view, test_image, mock_qpixmap, qtbot):
    """Test preprocessing image display."""
    qtbot.addWidget(results_view)
    
    # Update image
    stage = "Original"
    pixmap = mock_qpixmap
    results_view.update_preprocessing_image(stage, pixmap)
    
    # Verify image stored
    assert results_view.get_stage_image(stage) == pixmap
    
    # Verify label updated
    label = results_view.stage_labels[stage]
    label.setPixmap.assert_called_once()

def test_error_display(results_view, invalid_results):
    """Test error message display."""
    results_view.update_results(invalid_results)
    assert "Error:" in results_view.text_edit.toPlainText()
    assert invalid_results["error"] in results_view.text_edit.toPlainText()

def test_clear_results(results_view, test_results, mock_qpixmap):
    """Test clearing results and images."""
    # Add some data
    results_view.update_results(test_results)
    results_view.update_preprocessing_image("Original", mock_qpixmap)
    
    # Clear everything
    results_view.clear()
    
    # Verify cleared
    assert not results_view.text_edit.toPlainText()
    assert not results_view.preprocessing_images
    for bar in results_view.confidence_bars.values():
        assert bar.value() == 0
    
    # Verify each label is cleared exactly once
    for stage, label in results_view.stage_labels.items():
        label.clear.assert_called_once()
