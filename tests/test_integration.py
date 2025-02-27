"""
Integration test for VHS processing system.
"""
import os
import pytest
from unittest.mock import patch, Mock
from pathlib import Path

from src.models.coordinator import ProcessingCoordinator
from src.gui.results_view import ResultsView
from src.enrichment import api_client  # Import the module to patch correctly
from PyQt6.QtWidgets import QApplication

# Mock data
MOCK_MOVIE_DATA = {
    "title": "Back to the Future",
    "year": 1985,
    "runtime": 116,
    "genre": ["Adventure", "Science Fiction"],
    "director": "Robert Zemeckis",
    "cast": ["Michael J. Fox", "Christopher Lloyd"],
    "plot": "Marty McFly, a 17-year-old high school student, is accidentally sent thirty years into the past."
}

MOCK_AUDIO_DATA = {
    "artist": "Pink Floyd",
    "album": "The Wall",
    "year": 1979,
    "genre": ["Progressive Rock", "Rock"],
    "label": "Harvest Records",
    "format": "Vinyl",
    "tracks": ["Another Brick in the Wall", "Comfortably Numb"]
}

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

@pytest.fixture(autouse=True)
def setup_environment():
    """Set up test environment variables."""
    with patch.dict(os.environ, {
        'TMDB_API_KEY': 'dummy_tmdb_key',
        'DISCOGS_CONSUMER_KEY': 'dummy_discogs_key',
        'DISCOGS_CONSUMER_SECRET': 'dummy_discogs_secret'
    }, clear=True):  # Clear=True ensures no other env vars interfere
        yield

@patch('src.models.coordinator.search_movie_details')  # Patch at the point of use
@patch('src.vision.processor.VisionProcessor.process_image')
def test_movie_processing(mock_process_image, mock_search_movie, qapp):
    """Test complete movie processing pipeline."""
    # Configure mocks
    mock_process_image.return_value = MOCK_VISION_RESULT
    mock_search_movie.return_value = MOCK_MOVIE_DATA.copy()  # Use copy to prevent modification

    # Initialize components
    coordinator = ProcessingCoordinator()
    results_view = ResultsView()
    
    # Process test image
    test_image = str(Path("test_images") / "test_vhs_cover.jpg")
    results = coordinator.process_tape(test_image, debug=True)
    
    # Verify mock calls
    mock_process_image.assert_called_once()
    mock_search_movie.assert_called_once_with("Back to the Future (1985)")
    
    # Verify basic results structure
    assert results["success"]
    assert "extracted_titles" in results
    assert len(results["extracted_titles"]) > 0
    assert "vision_data" in results
    
    # Verify movie data integration
    assert "movie_data" in results
    movie_data = results["movie_data"]
    assert movie_data is not None
    assert movie_data["title"] == MOCK_MOVIE_DATA["title"]
    assert movie_data["year"] == MOCK_MOVIE_DATA["year"]
    assert movie_data["plot"] == MOCK_MOVIE_DATA["plot"]
    
    # Test GUI display
    results_view.update_results(results)
    
    # Verify movie tab content
    movie_text = results_view.movie_text.toPlainText()
    assert MOCK_MOVIE_DATA["title"] in movie_text
    assert str(MOCK_MOVIE_DATA["year"]) in movie_text
    assert MOCK_MOVIE_DATA["plot"][:50] in movie_text
    
    # Verify results saved
    assert "results_path" in results
    results_file = Path(results["results_path"])
    assert results_file.exists()

@patch('src.models.coordinator.search_audio_details')  # Patch at the point of use
@patch('src.vision.processor.VisionProcessor.process_image')
def test_audio_processing(mock_process_image, mock_search_audio, qapp):
    """Test complete audio processing pipeline."""
    # Configure mocks for audio media
    mock_process_image.return_value = {
        "success": True,
        "vision_data": MOCK_VISION_DATA,
        "texts": ["Pink Floyd - The Wall"],
        "debug_image": None
    }
    mock_search_audio.return_value = MOCK_AUDIO_DATA.copy()  # Use copy to prevent modification
    
    # Initialize components
    coordinator = ProcessingCoordinator()
    results_view = ResultsView()
    
    # Process test image
    test_image = str(Path("test_images") / "test_audio_cover.jpg")
    results = coordinator.process_tape(test_image, media_type="VINYL")
    
    # Verify mock calls
    mock_process_image.assert_called_once()
    mock_search_audio.assert_called_once_with("Pink Floyd - The Wall", "VINYL")
    
    # Verify audio data integration
    assert "audio_data" in results
    audio_data = results["audio_data"]
    assert audio_data is not None
    assert audio_data["artist"] == MOCK_AUDIO_DATA["artist"]
    assert audio_data["album"] == MOCK_AUDIO_DATA["album"]
    assert audio_data["year"] == MOCK_AUDIO_DATA["year"]
    
    # Test GUI display
    results_view.update_results(results)
    audio_text = results_view.audio_text.toPlainText()
    assert MOCK_AUDIO_DATA["artist"] in audio_text
    assert MOCK_AUDIO_DATA["album"] in audio_text
    
@patch('src.vision.processor.VisionProcessor.process_image')
def test_invalid_image_handling(mock_process_image, qapp):
    """Test handling of invalid image input."""
    # Configure mock to simulate error
    mock_process_image.return_value = {
        "success": False,
        "error": "Failed to load image: nonexistent.jpg"
    }
    
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
    """Test handling when no text is found in image."""
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

def test_missing_api_keys(qapp):
    """Test graceful handling when API keys are not configured."""
    # Test movie metadata without TMDB key
    with patch.dict('os.environ', {'TMDB_API_KEY': ''}):
        movie_data = api_client.search_movie_details("Back to the Future")
        assert movie_data["title"] is None
        assert movie_data["year"] is None
        
    # Test audio metadata without Discogs keys
    with patch.dict('os.environ', {
        'DISCOGS_CONSUMER_KEY': '',
        'DISCOGS_CONSUMER_SECRET': ''
    }):
        audio_data = api_client.search_audio_details("Pink Floyd - The Wall", "VINYL")
        assert audio_data["artist"] is None
        assert audio_data["album"] is None
