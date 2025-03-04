"""
API client for enriching media metadata.
"""
from typing import Dict, Any, Optional, List
import requests
import logging
from ..config.settings import (
    TMDB_API_KEY,
    DISCOGS_CONSUMER_KEY,
    DISCOGS_CONSUMER_SECRET
)

logger = logging.getLogger(__name__)

class TMDbClient:
    """Client for interacting with The Movie Database (TMDb) API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize TMDb client.
        
        Args:
            api_key: Optional API key. If not provided, uses TMDB_API_KEY from settings.
        """
        self.api_key = api_key or TMDB_API_KEY
        if not self.api_key:
            raise ValueError("TMDb API key is required")
        
        self.base_url = 'https://api.themoviedb.org/3'
    
    def search_movies(self, query: str) -> List[Dict[str, Any]]:
        """Search for movies by title.
        
        Args:
            query: Movie title to search for
            
        Returns:
            List of movie search results
        """
        try:
            response = requests.get(
                f'{self.base_url}/search/movie',
                params={
                    'api_key': self.api_key,
                    'query': query,
                    'language': 'en-US',
                    'page': 1,
                    'include_adult': False
                }
            )
            
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
            
        except Exception as e:
            logger.error(f"Error searching movies: {e}")
            return []
    
    def get_movie(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific movie.
        
        Args:
            movie_id: TMDb movie ID
            
        Returns:
            Movie details dictionary, or None if not found/error
        """
        try:
            response = requests.get(
                f'{self.base_url}/movie/{movie_id}',
                params={
                    'api_key': self.api_key,
                    'language': 'en-US',
                    'append_to_response': 'credits'
                }
            )
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting movie details: {e}")
            return None

def create_empty_movie_result() -> Dict[str, Any]:
    """Create empty movie result structure."""
    return {
        'title': None,
        'year': None,
        'runtime': None,
        'genre': None,
        'director': None,
        'cast': [],
        'plot': None
    }

def create_empty_audio_result() -> Dict[str, Any]:
    """Create empty audio result structure."""
    return {
        'artist': None,
        'album': None,
        'year': None,
        'genre': None,
        'label': None,
        'format': None,
        'tracks': []
    }

def search_movie_details(text: str) -> Dict[str, Any]:
    """
    Search for movie details using TMDB API.
    
    Args:
        text: Extracted text from media cover
        
    Returns:
        Dictionary of movie details (empty if no API key or error)
    """
    # Default empty results
    results = create_empty_movie_result()
    
    if not TMDB_API_KEY:
        logger.warning("No TMDB API key configured")
        return results
        
    try:
        # Extract potential title from first few lines
        potential_title = text.split('\n')[0].strip()
        
        # Search TMDB
        response = requests.get(
            'https://api.themoviedb.org/3/search/movie',
            params={
                'api_key': TMDB_API_KEY,
                'query': potential_title,
                'language': 'en-US',
                'page': 1,
                'include_adult': False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                movie = data['results'][0]
                
                # Get additional details
                movie_id = movie['id']
                details = requests.get(
                    f'https://api.themoviedb.org/3/movie/{movie_id}',
                    params={
                        'api_key': TMDB_API_KEY,
                        'language': 'en-US',
                        'append_to_response': 'credits'
                    }
                ).json()
                
                # Update results
                results.update({
                    'title': movie['title'],
                    'year': int(movie['release_date'][:4]) if movie.get('release_date') else None,
                    'runtime': details.get('runtime'),
                    'genre': [g['name'] for g in details.get('genres', [])],
                    'plot': movie['overview'],
                })
                
                # Get credits
                if 'credits' in details:
                    # Get director
                    directors = [
                        crew['name'] for crew in details['credits'].get('crew', [])
                        if crew['job'].lower() == 'director'
                    ]
                    if directors:
                        results['director'] = directors[0]
                    
                    # Get cast
                    cast = details['credits'].get('cast', [])
                    results['cast'] = [
                        person['name'] for person in cast[:5]  # Top 5 cast members
                    ]
                
    except Exception as e:
        logger.error(f"Error fetching movie details: {e}")
        
    return results

def search_audio_details(text: str, media_type: str) -> Dict[str, Any]:
    """
    Search for audio media details using Discogs API.
    
    Args:
        text: Extracted text from media cover
        media_type: Type of audio media (CD, VINYL, CASSETTE)
        
    Returns:
        Dictionary of audio details (empty if no API key or error)
    """
    results = create_empty_audio_result()
    
    if not (DISCOGS_CONSUMER_KEY and DISCOGS_CONSUMER_SECRET):
        logger.warning("No Discogs API credentials configured")
        return results
        
    try:
        # Extract potential artist/album from first few lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) >= 2:
            potential_artist = lines[0]
            potential_album = lines[1]
            
            # Common headers for all requests
            headers = {
                'User-Agent': 'MediaProcessor/1.0',
                'Authorization': f'Discogs key={DISCOGS_CONSUMER_KEY}, secret={DISCOGS_CONSUMER_SECRET}'
            }
            
            # Search Discogs
            response = requests.get(
                'https://api.discogs.com/database/search',
                params={
                    'artist': potential_artist,
                    'release_title': potential_album,
                    'type': 'release'
                },
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    release = data['results'][0]
                    
                    # Get detailed release info
                    release_id = release['id']
                    details = requests.get(
                        f'https://api.discogs.com/releases/{release_id}',
                        headers=headers
                    ).json()
                    
                    # Update results
                    results.update({
                        'artist': details.get('artists_sort'),
                        'album': details.get('title'),
                        'year': details.get('year'),
                        'genre': details.get('genres', []),
                        'label': details.get('labels', [{}])[0].get('name'),
                        'format': details.get('formats', [{}])[0].get('name'),
                        'tracks': [
                            track['title']
                            for track in details.get('tracklist', [])
                        ]
                    })
                    
    except Exception as e:
        logger.error(f"Error fetching audio details: {e}")
        
    return results
