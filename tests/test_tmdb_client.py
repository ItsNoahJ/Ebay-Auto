"""
Tests for TMDB API client functionality.
"""
import os
import pytest
from unittest.mock import patch
from src.enrichment.tmdb_client import TMDBClient

@pytest.fixture
def tmdb_client(tmp_path):
    """Create a TMDB client with temporary cache file."""
    cache_path = str(tmp_path / "test_cache.sqlite")
    return TMDBClient(cache_path=cache_path)

@pytest.fixture
def mock_response():
    """Sample movie search response."""
    return {
        "results": [
            {
                "id": 123,
                "title": "Test Movie",
                "release_date": "1995-01-01",
                "overview": "A test movie description"
            }
        ]
    }

def test_init_requires_api_key():
    """Test that client requires API key."""
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValueError):
            TMDBClient()

def test_search_movie(tmdb_client, mock_response):
    """Test movie search functionality."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        
        results = tmdb_client.search_movie("Test Movie")
        assert results == mock_response
        
        # Verify API call
        mock_get.assert_called_once()
        args = mock_get.call_args
        assert "query=Test+Movie" in args[1]["params"].values()

def test_get_movie(tmdb_client):
    """Test getting movie details."""
    movie_data = {
        "id": 123,
        "title": "Test Movie",
        "release_date": "1995-01-01",
        "overview": "A test movie description"
    }
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = movie_data
        mock_get.return_value.status_code = 200
        
        result = tmdb_client.get_movie(123)
        assert result == movie_data
        
        # Verify API call
        mock_get.assert_called_once()
        assert "/movie/123" in mock_get.call_args[0][0]

def test_caching(tmdb_client, mock_response):
    """Test that responses are cached and reused."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        
        # First call should hit the API
        tmdb_client.search_movie("Test Movie")
        assert mock_get.call_count == 1
        
        # Second call should use cache
        tmdb_client.search_movie("Test Movie")
        assert mock_get.call_count == 1  # Count shouldn't increase

def test_find_best_match_exact(tmdb_client):
    """Test finding best match with exact title."""
    search_response = {
        "results": [
            {
                "id": 123,
                "title": "Test Movie",
                "release_date": "1995-01-01"
            }
        ]
    }
    
    movie_details = {
        "id": 123,
        "title": "Test Movie",
        "release_date": "1995-01-01",
        "overview": "A test movie description"
    }
    
    with patch.object(tmdb_client, 'search_movie') as mock_search:
        with patch.object(tmdb_client, 'get_movie') as mock_get:
            mock_search.return_value = search_response
            mock_get.return_value = movie_details
            
            result = tmdb_client.find_best_match("Test Movie", year=1995)
            assert result == movie_details
            mock_search.assert_called_once()
            mock_get.assert_called_once()

def test_find_best_match_no_results(tmdb_client):
    """Test finding best match with no results."""
    with patch.object(tmdb_client, 'search_movie') as mock_search:
        mock_search.return_value = {"results": []}
        
        result = tmdb_client.find_best_match("Nonexistent Movie")
        assert result is None
        mock_search.assert_called_once()

def test_retry_logic(tmdb_client):
    """Test API retry logic on failure."""
    with patch('requests.get') as mock_get:
        # Make first two calls fail, third succeed
        mock_get.side_effect = [
            requests.exceptions.RequestException(),
            requests.exceptions.RequestException(),
            type('Response', (), {
                'json': lambda: {"results": []},
                'raise_for_status': lambda: None,
                'status_code': 200
            })()
        ]
        
        result = tmdb_client.search_movie("Test Movie")
        assert result == {"results": []}
        assert mock_get.call_count == 3
