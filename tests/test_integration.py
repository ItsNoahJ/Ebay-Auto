"""
Integration test for VHS processing system.
"""
import os
import pytest
from unittest.mock import patch
from pathlib import Path

from src.models.coordinator import ProcessingCoordinator
from src.gui.results_view import ResultsView
from src.enrichment.api_client import TMDbClient
from PyQt6.QtWidgets import QApplication

# Mock data
MOCK_MOVIE_DATA = {
    "title": "Back to the Future",
    "release_date": "1985-07-03",
    "overview": "Marty McFly, a 17-year-old high school student, is accidentally sent thirty years into the past.",
    "vote_average": 8.5,
    "genres": [{"name": "Adventure"}, {"name": "Science Fiction"}]
}

MOCK_SEARCH_RESULTS = [{
    "id": 105,
    "title": "Back to the Future",
    "release_date": "1985-07-03"
}]

# Mock vision processing results
MOCK_VISION_DATA = {
    "image_size": (800, 1200),
    "sharpness": 85.5,
    "rectangles": 1,
    "text_regions": ["Back to the Future (1985)"],
    "processing_time": 0.5
}

MOCK_VISION_RESULT = {
    "success": True,
    "vision_data": MOCK_VISION_DATA,
    "texts": ["Back to the Future (1985)"],
    "debug_image": None
}

# Set up Qt application for GUI tests
@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance."""
    os.environ["QT_QPA_PLATFORM"] = "minimal"  # Headless testing
    app = QApplication([])
    yield app
    app.quit()

@patch('src.enrichment.api_client.TMDbClient.get_movie')
@patch('src.enrichment.api_client.TMDbClient.search_movies')
@patch('src.vision.processor.VisionProcessor.process_image')
def test_end_to_end_processing(mock_process_image, mock_search, mock_get_movie, qapp):
    # Configure mocks
    mock_process_image.return_value = MOCK_VISION_RESULT
    mock_search.return_value = MOCK_SEARCH_RESULTS
    mock_get_movie.return_value = MOCK_MOVIE_DATA
    """Test complete processing pipeline."""
    # Initialize components
    coordinator = ProcessingCoordinator()
    results_view = ResultsView()
    
    # Process test image
    test_image = str(Path("test_images") / "test_vhs_cover.jpg")
    results = coordinator.process_tape(test_image, debug=True)
    
    # Verify basic results structure
    assert results["success"]
    assert "extracted_titles" in results
    assert len(results["extracted_titles"]) > 0
    assert "vision_data" in results
    
    # Verify TMDB integration
    assert "movie_data" in results
    movie_data = results["movie_data"]
    assert movie_data is not None
    assert "title" in movie_data
    assert "release_date" in movie_data
    assert "overview" in movie_data
    
    # Test GUI display
    results_view.update_results(results)
    
    # Verify movie tab content
    movie_text = results_view.movie_text.toPlainText()
    assert movie_data["title"] in movie_text
    assert movie_data["release_date"][:4] in movie_text
    assert movie_data["overview"][:50] in movie_text
    
    # Verify results saved
    assert "results_path" in results
    results_file = Path(results["results_path"])
    assert results_file.exists()
    
@patch('src.vision.processor.VisionProcessor.process_image')
def test_invalid_image_handling(mock_process_image, qapp):
    # Configure mock to simulate error
    mock_process_image.return_value = {
        "success": False,
        "error": "Failed to load image: nonexistent.jpg"
    }
    """Test handling of invalid image input."""
    coordinator = ProcessingCoordinator()
    results_view = ResultsView()
    
    # Process non-existent image
    results = coordinator.process_tape("nonexistent.jpg")
    
    # Verify error handling
    assert not results["success"]
    assert "error" in results
    
    # Test GUI handles error gracefully
    results_view.update_results(results)
    assert "No movie data" in results_view.movie_text.toPlainText()
    
@patch('src.vision.processor.VisionProcessor.process_image')
def test_no_text_found_handling(mock_process_image, qapp):
    # Configure mock for no text found
    mock_process_image.return_value = {
        "success": True,
        "vision_data": {
            "image_size": (100, 100),
            "sharpness": 0.0,
            "rectangles": 0,
            "text_regions": [],
            "processing_time": 0.1
        },
        "texts": [],
        "debug_image": None
    }
    """Test handling when no text is found in image."""
    coordinator = ProcessingCoordinator()
    results_view = ResultsView()
    
    # Create blank test image
    test_image = str(Path("test_images") / "blank.jpg")
    if not Path(test_image).exists():
        # Create a small blank image for testing
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='white')
        img.save(test_image)
    
    # Process blank image
    results = coordinator.process_tape(test_image)
    
    # Verify graceful handling
    assert results["success"]
    assert len(results.get("extracted_titles", [])) == 0
    
    # Test GUI handles no text gracefully
    results_view.update_results(results)
    assert "No text extracted" in results_view.text_area.toPlainText()
