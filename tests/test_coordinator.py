"""
Processing coordinator tests.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.coordinator import ProcessingCoordinator

@pytest.fixture
def coordinator():
    """Create coordinator instance."""
    return ProcessingCoordinator()

def test_extract_year():
    """Test year extraction."""
    coordinator = ProcessingCoordinator()
    
    # Test valid years
    assert coordinator.extract_year("Movie (1995)") == 1995
    assert coordinator.extract_year("Released in 2020!") == 2020
    assert coordinator.extract_year("19th century") is None
    assert coordinator.extract_year("2525") is None  # Future year
    assert coordinator.extract_year("1800") is None  # Too old
    assert coordinator.extract_year("No year here") is None

def test_extract_title_candidates():
    """Test title extraction."""
    coordinator = ProcessingCoordinator()
    
    # Test single line
    texts = ["The Movie Title"]
    candidates = coordinator.extract_title_candidates(texts)
    assert len(candidates) == 1
    assert candidates[0] == "The Movie Title"
    
    # Test multiple lines
    texts = [
        "The Movie\nTitle (1995)\nStudio Name"
    ]
    candidates = coordinator.extract_title_candidates(texts)
    assert len(candidates) == 3
    assert "The Movie" in candidates
    assert "Title (1995)" in candidates
    assert "Studio Name" in candidates
    
    # Test short lines
    texts = ["A", "The Movie", "B"]
    candidates = coordinator.extract_title_candidates(texts)
    assert len(candidates) == 1
    assert candidates[0] == "The Movie"

@patch("src.models.coordinator.TMDbClient")
def test_find_best_title(mock_tmdb):
    """Test title matching."""
    coordinator = ProcessingCoordinator()
    
    # Mock API response
    mock_movie = {
        "id": 1,
        "title": "Test Movie",
        "popularity": 10.0
    }
    
    mock_tmdb.return_value.get_best_match.return_value = mock_movie
    
    # Test single title
    candidates = ["Test Movie"]
    result = coordinator.find_best_title(candidates)
    assert result == mock_movie
    
    # Test multiple titles
    mock_tmdb.return_value.get_best_match.side_effect = [
        {"id": 1, "title": "Movie A", "popularity": 5.0},
        {"id": 2, "title": "Movie B", "popularity": 10.0}
    ]
    
    candidates = ["Movie A", "Movie B"]
    result = coordinator.find_best_title(candidates)
    assert result["title"] == "Movie B"  # Higher popularity
    
    # Test no matches
    mock_tmdb.return_value.get_best_match.return_value = None
    
    candidates = ["Unknown Movie"]
    result = coordinator.find_best_title(candidates)
    assert result is None

@patch("src.models.coordinator.VisionProcessor")
@patch("src.models.coordinator.TMDbClient")
def test_process_tape(mock_tmdb, mock_vision, tmp_path):
    """Test tape processing."""
    coordinator = ProcessingCoordinator()
    
    # Create test image
    image_path = str(tmp_path / "test.jpg")
    Path(image_path).touch()
    
    # Mock vision results
    mock_vision.return_value.process_image.return_value = {
        "success": True,
        "vision_data": {
            "image_size": "640x480",
            "sharpness": 100.0,
            "rectangles": 1,
            "text_regions": 2,
            "processing_time": 1.0
        },
        "texts": ["Test Movie (1995)"]
    }
    
    # Mock movie data
    mock_tmdb.return_value.get_best_match.return_value = {
        "id": 1,
        "title": "Test Movie",
        "release_date": "1995-01-01",
        "popularity": 10.0
    }
    
    # Test successful processing
    results = coordinator.process_tape(image_path)
    
    assert results["success"]
    assert "vision_data" in results
    assert "extracted_titles" in results
    assert "movie_data" in results
    
    # Test with debug
    results = coordinator.process_tape(image_path, debug=True)
    
    assert results["success"]
    assert "debug_image" in mock_vision.return_value.process_image.call_args[1]
    
    # Test vision failure
    mock_vision.return_value.process_image.return_value = {
        "success": False,
        "error": "Test error"
    }
    
    results = coordinator.process_tape(image_path)
    
    assert not results["success"]
    assert "error" in results
