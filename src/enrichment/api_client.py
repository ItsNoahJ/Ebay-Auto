"""
API client for enriching media metadata.
"""
from typing import Dict, Any, Optional
import requests
from ..config.settings import TMDB_API_KEY, DISCOGS_API_KEY

def search_movie_details(text: str) -> Dict[str, Any]:
    """
    Search for movie details using TMDB API.
    
    Args:
        text: Extracted text from media cover
        
    Returns:
        Dictionary of movie details
    """
    # Default empty results
    results = {
        'title': None,
        'year': None,
        'runtime': None,
        'genre': None,
        'director': None,
        'cast': [],
        'plot': None
    }
    
    if not TMDB_API_KEY:
        print("Warning: TMDB_API_KEY not set")
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
        print(f"Error fetching movie details: {e}")
        
    return results

def search_audio_details(text: str, media_type: str) -> Dict[str, Any]:
    """
    Search for audio media details using Discogs API.
    
    Args:
        text: Extracted text from media cover
        media_type: Type of audio media (CD, VINYL, CASSETTE)
        
    Returns:
        Dictionary of audio details
    """
    results = {
        'artist': None,
        'album': None,
        'year': None,
        'genre': None,
        'label': None,
        'format': None,
        'tracks': []
    }
    
    if not DISCOGS_API_KEY:
        print("Warning: DISCOGS_API_KEY not set")
        return results
        
    try:
        # Extract potential artist/album from first few lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) >= 2:
            potential_artist = lines[0]
            potential_album = lines[1]
            
            # Search Discogs
            response = requests.get(
                'https://api.discogs.com/database/search',
                params={
                    'key': DISCOGS_API_KEY,
                    'artist': potential_artist,
                    'release_title': potential_album,
                    'type': 'release'
                },
                headers={'User-Agent': 'MediaProcessor/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    release = data['results'][0]
                    
                    # Get detailed release info
                    release_id = release['id']
                    details = requests.get(
                        f'https://api.discogs.com/releases/{release_id}',
                        headers={'User-Agent': 'MediaProcessor/1.0'}
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
        print(f"Error fetching audio details: {e}")
        
    return results
