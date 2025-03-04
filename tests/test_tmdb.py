"""
Test TMDb API client functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.enrichment.api_client import TMDbClient

@pytest.fixture
def mock_tmdb_response():
    """Mock response data for TMDb API."""
    return {
        'results': [
            {
                'id': 105,
                'title': 'Back to the Future',
                'release_date': '1985-07-03',
                'overview': 'Test overview'
            }
        ]
    }

@pytest.fixture
def mock_movie_details():
    """Mock movie details response."""
    return {
        'id': 105,
        'title': 'Back to the Future',
        'runtime': 116,
        'overview': 'Test overview',
        'credits': {
            'crew': [{'job': 'Director', 'name': 'Robert Zemeckis'}],
            'cast': [{'name': 'Michael J. Fox'}, {'name': 'Christopher Lloyd'}]
        }
    }

@pytest.mark.unit
def test_search_movies(mock_tmdb_response):
    """Test movie search functionality."""
    with patch('requests.get') as mock_get:
        # Configure mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_tmdb_response
        mock_get.return_value = mock_response

        client = TMDbClient('dummy_key')
        results = client.search_movies("Back to the Future")
        
        # Verify we got results
        assert results
        assert len(results) > 0
        
        # Check first result has expected fields
        first_movie = results[0]
        assert first_movie['id'] == 105
        assert first_movie['title'] == 'Back to the Future'
        assert first_movie['release_date'] == '1985-07-03'
    
@pytest.mark.unit
def test_get_movie(mock_movie_details):
    """Test getting detailed movie information."""
    with patch('requests.get') as mock_get:
        # Configure mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_movie_details
        mock_get.return_value = mock_response

        client = TMDbClient('dummy_key')
        movie = client.get_movie(105)
        
        # Verify response
        assert movie is not None
        assert movie['id'] == 105
        assert movie['title'] == 'Back to the Future'
        assert movie['runtime'] == 116
        assert movie['overview'] == 'Test overview'
    
@pytest.mark.unit
def test_invalid_movie_search():
    """Test searching with invalid query."""
    with patch('requests.get') as mock_get:
        # Configure mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'results': []}
        mock_get.return_value = mock_response
        
        client = TMDbClient('dummy_key')
        results = client.search_movies("xyzabc123nonexistentmovie")
        
        # Should return empty list, not None
        assert isinstance(results, list)
        assert len(results) == 0
    
@pytest.mark.unit
def test_invalid_movie_id():
    """Test getting invalid movie ID."""
    with patch('requests.get') as mock_get:
        # Configure mock response for 404
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        client = TMDbClient('dummy_key')
        result = client.get_movie(9999999999)
        
        # Should return None
        assert result is None

@pytest.mark.unit
def test_tmdb_client_no_api_key():
    """Test TMDb client initialization without API key."""
    with patch('src.enrichment.api_client.TMDB_API_KEY', None):
        with pytest.raises(ValueError):
            TMDbClient()
