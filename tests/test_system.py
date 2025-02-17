"""
System integration tests.
"""
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.models.coordinator import ProcessingCoordinator


@pytest.fixture
def test_env(tmp_path):
    """Set up test environment."""
    # Create paths
    (tmp_path / "storage").mkdir()
    (tmp_path / "storage/cache").mkdir()
    (tmp_path / "storage/images").mkdir()
    (tmp_path / "storage/results").mkdir()
    (tmp_path / "storage/debug").mkdir()
    
    # Configure env
    env = {
        "TESSERACT_CMD": "tesseract",
        "TMDB_API_KEY": "test_key",
        "VISION_TARGET_WIDTH": "1920",
        "VISION_MIN_COVER_AREA": "10000",
        "VISION_MAX_COVER_RATIO": "0.8",
        "VISION_EPSILON_FACTOR": "0.02",
        "CAMERA_DEVICE_ID": "0",
        "GUI_WINDOW_WIDTH": "1280",
        "GUI_WINDOW_HEIGHT": "720",
        "GUI_THEME": "light",
        "API_TIMEOUT": "10",
        "API_MAX_RETRIES": "3",
        "API_RATE_LIMIT": "40",
        "API_RATE_WINDOW": "10",
        "API_CACHE_TTL": "86400"
    }
    
    with patch.dict(os.environ, env):
        yield tmp_path

def test_image_processing(test_env):
    """Test full image processing workflow."""
    # Create test image
    from src.create_test_image import create_test_image
    
    image_path = test_env / "test.jpg"
    create_test_image(
        "Test Movie",
        "1995",
        output_path=str(image_path)
    )
    
    assert image_path.exists()
    
    # Mock TMDb API
    movie_data = {
        "id": 123,
        "title": "Test Movie",
        "release_date": "1995-01-01",
        "vote_average": 8.5,
        "genres": [
            {"id": 1, "name": "Action"},
            {"id": 2, "name": "Adventure"}
        ],
        "overview": "Test movie description."
    }
    
    with patch("src.enrichment.api_client.TMDbClient.search_movies") as mock_search, \
         patch("src.enrichment.api_client.TMDbClient.get_movie") as mock_get:
             
        # Configure mocks
        mock_search.return_value = [movie_data]
        mock_get.return_value = movie_data
        
        # Process image
        coordinator = ProcessingCoordinator()
        results = coordinator.process_tape(str(image_path), debug=True)
        
        # Check results
        assert results["success"]
        assert len(results["texts"]) > 0
        assert "Test Movie" in results["extracted_titles"][0]
        assert "1995" in results["extracted_titles"][0]
        assert results["movie_data"] == movie_data
        assert Path(results["debug_image"]).exists()
        assert Path(results["results_path"]).exists()
        
def test_error_handling(test_env):
    """Test error handling."""
    coordinator = ProcessingCoordinator()
    
    # Test invalid image
    results = coordinator.process_tape("nonexistent.jpg")
    assert not results["success"]
    assert "error" in results
    
    # Test API error
    with patch("src.enrichment.api_client.TMDbClient.search_movies") as mock_search:
        mock_search.side_effect = Exception("API error")
        
        results = coordinator.process_tape(
            str(test_env / "test.jpg")
        )
        assert not results["success"]
        assert "error" in results
