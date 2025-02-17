"""
TMDb API client module.
"""
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
import requests_cache

from ..config.settings import API_SETTINGS, STORAGE_PATHS

class TMDbClient:
    """TMDb API client."""
    
    # Base URL
    BASE_URL = "https://api.themoviedb.org/3"
    
    def __init__(self):
        """Initialize client."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self.api_key = API_SETTINGS["tmdb_api_key"]
        self.last_request = 0
        self.requests_this_window = 0
        
        # Configure cache
        cache_path = STORAGE_PATHS["cache"] / "tmdb_cache"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        requests_cache.install_cache(
            str(cache_path),
            backend="sqlite",
            expire_after=API_SETTINGS["cache_ttl"]
        )
        
    def _enforce_rate_limit(self):
        """Enforce API rate limiting."""
        # Get current time
        now = time.time()
        
        # Check if we're in a new window
        window_size = API_SETTINGS["rate_window"]
        
        if now - self.last_request > window_size:
            self.requests_this_window = 0
            
        # Check rate limit
        rate_limit = API_SETTINGS["rate_limit"]
        
        if self.requests_this_window >= rate_limit:
            # Calculate sleep time
            sleep_time = window_size - (now - self.last_request)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                
            # Reset counter
            self.requests_this_window = 0
            
        # Update state
        self.last_request = now
        self.requests_this_window += 1
        
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make API request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data if successful, None otherwise
        """
        try:
            # Enforce rate limit
            self._enforce_rate_limit()
            
            # Add API key
            if params is None:
                params = {}
                
            params["api_key"] = self.api_key
            
            # Make request
            url = f"{self.BASE_URL}/{endpoint}"
            
            for attempt in range(API_SETTINGS["max_retries"]):
                try:
                    response = requests.get(
                        url,
                        params=params,
                        timeout=API_SETTINGS["timeout"]
                    )
                    
                    # Check status
                    response.raise_for_status()
                    
                    return response.json()
                    
                except requests.RequestException as e:
                    if attempt == API_SETTINGS["max_retries"] - 1:
                        raise
                    
                    # Wait before retry
                    time.sleep(2 ** attempt)
                    
        except Exception as e:
            self.logger.exception("Request error")
            return None
            
    def search_movies(self, query: str) -> List[Dict]:
        """
        Search for movies.
        
        Args:
            query: Search query
            
        Returns:
            List of movie results
        """
        # Make request
        data = self._make_request(
            "search/movie",
            {"query": query}
        )
        
        if not data:
            return []
            
        return data.get("results", [])
        
    def get_movie(self, movie_id: int) -> Optional[Dict]:
        """
        Get movie details.
        
        Args:
            movie_id: TMDb movie ID
            
        Returns:
            Movie data if found, None otherwise
        """
        return self._make_request(f"movie/{movie_id}")
