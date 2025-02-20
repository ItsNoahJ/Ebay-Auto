"""
Test TMDb API client functionality.
"""
import pytest
from src.enrichment.api_client import TMDbClient

def test_search_movies():
    """Test movie search functionality."""
    client = TMDbClient()
    
    # Test with a known movie title
    results = client.search_movies("Back to the Future")
    
    # Verify we got results
    assert results
    assert len(results) > 0
    
    # Check first result has expected fields
    first_movie = results[0]
    assert "id" in first_movie
    assert "title" in first_movie
    assert "release_date" in first_movie
    
def test_get_movie():
    """Test getting detailed movie information."""
    client = TMDbClient()
    
    # Back to the Future's TMDb ID
    movie_id = 105
    
    # Get movie details
    movie = client.get_movie(movie_id)
    
    # Verify response
    assert movie is not None
    assert movie["id"] == movie_id
    assert movie["title"] == "Back to the Future"
    assert "runtime" in movie
    assert "overview" in movie
    
def test_invalid_movie_search():
    """Test searching with invalid query."""
    client = TMDbClient()
    
    # Search with unlikely string
    results = client.search_movies("xyzabc123nonexistentmovie")
    
    # Should return empty list, not None
    assert isinstance(results, list)
    assert len(results) == 0
    
def test_invalid_movie_id():
    """Test getting invalid movie ID."""
    client = TMDbClient()
    
    # Try to get nonexistent movie
    result = client.get_movie(9999999999)
    
    # Should return None
    assert result is None
