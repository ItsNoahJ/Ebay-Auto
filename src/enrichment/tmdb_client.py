"""
TMDB API client with caching support for movie metadata enrichment.
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlite3
from urllib.parse import quote

class TMDBClient:
    """
    Client for The Movie Database (TMDB) API with built-in caching.
    """
    def __init__(self, cache_path: str = "storage/cache/tmdb_cache.sqlite"):
        self.api_key = os.getenv("TMDB_API_KEY")
        self.enabled = bool(self.api_key)
        self.base_url = "https://api.themoviedb.org/3"
        self.cache_path = cache_path
        
        # Always init cache since it's needed for other operations
        self._init_cache()
        
        if self.enabled:
            # Only validate if we have an API key
            self._validate_api_key()
        
    def _validate_api_key(self):
        """Validate the API key by making a test request."""
        try:
            response = requests.get(
                f"{self.base_url}/configuration",
                params={"api_key": self.api_key},
                timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 401:
                raise ValueError("Invalid TMDB API key. Please check your API key and try again.") from e
            raise ValueError(f"Failed to validate TMDB API key: {str(e)}") from e
        
    def _init_cache(self):
        """Initialize the SQLite cache database."""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        
        conn = sqlite3.connect(self.cache_path)
        c = conn.cursor()
        
        # Create cache table if it doesn't exist
        c.execute('''
            CREATE TABLE IF NOT EXISTS tmdb_cache (
                query TEXT PRIMARY KEY,
                response TEXT,
                timestamp DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def _get_cached(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response for a query.
        
        Args:
            query: API query string
            
        Returns:
            Cached response if valid, None otherwise
        """
        conn = sqlite3.connect(self.cache_path)
        c = conn.cursor()
        
        # Get cached response
        c.execute(
            "SELECT response, timestamp FROM tmdb_cache WHERE query = ?",
            (query,)
        )
        result = c.fetchone()
        conn.close()
        
        if not result:
            return None
            
        response, timestamp = result
        cache_time = datetime.fromisoformat(timestamp)
        
        # Check if cache is still valid (24 hours)
        if datetime.utcnow() - cache_time > timedelta(hours=24):
            return None
            
        return json.loads(response)
        
    def _cache_response(self, query: str, response: Dict[str, Any]):
        """
        Cache an API response.
        
        Args:
            query: API query string
            response: Response data to cache
        """
        conn = sqlite3.connect(self.cache_path)
        c = conn.cursor()
        
        # Store response with current timestamp
        c.execute(
            """
            INSERT OR REPLACE INTO tmdb_cache (query, response, timestamp)
            VALUES (?, ?, ?)
            """,
            (
                query,
                json.dumps(response),
                datetime.utcnow().isoformat()
            )
        )
        
        conn.commit()
        conn.close()
        
    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make an API request with retry logic.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            requests.exceptions.RequestException: If request fails after retries
        """
        if params is None:
            params = {}
            
        params["api_key"] = self.api_key
        
        # Build cache key from endpoint and params
        cache_key = f"{endpoint}?{quote(json.dumps(params, sort_keys=True))}"
        
        # Check cache first
        cached = self._get_cached(cache_key)
        if cached:
            return cached
            
        # Make API request with retries
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                # Cache successful response
                self._cache_response(cache_key, data)
                
                return data
                
            except requests.exceptions.RequestException:
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay)
                
    def search_movie(
        self,
        query: str,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for a movie.
        
        Args:
            query: Movie title to search for
            year: Optional release year to filter by
            
        Returns:
            Search results or empty dict if TMDB is disabled
        """
        if not self.enabled:
            return {"results": []}
            
        params = {"query": query}
        if year:
            params["year"] = year
            
        return self._make_request("/search/movie", params)
        
    def get_movie(self, movie_id: int) -> Dict[str, Any]:
        """
        Get detailed movie information.
        
        Args:
            movie_id: TMDB movie ID
            
        Returns:
            Movie details or empty dict if TMDB is disabled
        """
        if not self.enabled:
            return {}
            
        return self._make_request(f"/movie/{movie_id}")
        
    def find_best_match(
        self,
        title: str,
        year: Optional[int] = None,
        threshold: float = 0.6
    ) -> Optional[Dict[str, Any]]:
        """
        Find best matching movie based on title and year.
        
        Args:
            title: Movie title to search for
            year: Optional release year
            threshold: Minimum similarity score (0-1) for a match
            
        Returns:
            Best matching movie or None if no good match found
        """
        if not self.enabled:
            return None
            
        from difflib import SequenceMatcher
        
        # Search for movies
        results = self.search_movie(title, year)
        
        if not results.get("results"):
            return None
            
        # Score each result
        best_match = None
        best_score = 0
        
        for movie in results["results"]:
            # Calculate title similarity
            similarity = SequenceMatcher(
                None,
                title.lower(),
                movie["title"].lower()
            ).ratio()
            
            # Boost score if year matches
            if year and movie.get("release_date"):
                movie_year = int(movie["release_date"][:4])
                if movie_year == year:
                    similarity += 0.2
                    
            if similarity > best_score:
                best_score = similarity
                best_match = movie
                
        # Return best match if it meets threshold
        if best_score >= threshold:
            return self.get_movie(best_match["id"])
            
        return None
