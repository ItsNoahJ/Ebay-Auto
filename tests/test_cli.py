"""
CLI interface tests.
"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.cli import process_image, main

@pytest.fixture
def test_image(tmp_path):
    """Create test image file."""
    image_path = tmp_path / "test.jpg"
    image_path.touch()
    return str(image_path)

@pytest.fixture
def mock_results():
    """Create mock processing results."""
    return {
        "success": True,
        "vision_data": {
            "image_size": "640x480",
            "rectangles": 1,
            "text_regions": 2,
            "sharpness": 100.0,
            "processing_time": 1.0
        },
        "extracted_titles": ["Test Movie (1995)"],
        "movie_data": {
            "title": "Test Movie",
            "release_date": "1995-01-01",
            "vote_average": 8.5,
            "genres": [
                {"name": "Action"},
                {"name": "Adventure"}
            ],
            "overview": "Test movie description."
        }
    }

@patch("src.cli.ProcessingCoordinator")
def test_process_image(mock_coordinator, test_image, mock_results, capsys):
    """Test image processing."""
    # Mock successful processing
    mock_coordinator.return_value.process_tape.return_value = mock_results
    
    # Process image
    success = process_image(test_image)
    assert success
    
    # Check output
    captured = capsys.readouterr()
    assert "Vision Data:" in captured.out
    assert "640x480" in captured.out
    assert "Extracted Titles:" in captured.out
    assert "Test Movie (1995)" in captured.out
    assert "Movie Data:" in captured.out
    assert "Test Movie" in captured.out
    assert "8.5/10" in captured.out
    assert "Action, Adventure" in captured.out
    
    # Test debug mode
    success = process_image(test_image, debug=True)
    assert success
    
    # Test failure
    mock_coordinator.return_value.process_tape.return_value = {
        "success": False,
        "error": "Test error"
    }
    
    success = process_image(test_image)
    assert not success
    
    captured = capsys.readouterr()
    assert "Test error" in captured.err

@patch("src.cli.process_image")
@patch("src.cli.validate_settings")
def test_main_success(mock_validate, mock_process, test_image):
    """Test successful main execution."""
    # Mock success
    mock_process.return_value = True
    
    # Run with image path
    with patch("sys.argv", ["cli.py", test_image]):
        assert main() == 0
        
    mock_validate.assert_called_once()
    mock_process.assert_called_with(test_image, False)
    
    # Run with debug flag
    with patch("sys.argv", ["cli.py", test_image, "--debug"]):
        assert main() == 0
        
    mock_process.assert_called_with(test_image, True)

@patch("src.cli.process_image")
@patch("src.cli.validate_settings")
def test_main_failure(mock_validate, mock_process, test_image):
    """Test main execution failures."""
    # Test processing failure
    mock_process.return_value = False
    
    with patch("sys.argv", ["cli.py", test_image]):
        assert main() == 1
        
    # Test validation error
    mock_validate.side_effect = ValueError("Test error")
    
    with patch("sys.argv", ["cli.py", test_image]):
        assert main() == 1

def test_main_no_args():
    """Test main with no arguments."""
    with patch("sys.argv", ["cli.py"]):
        with pytest.raises(SystemExit):
            main()
