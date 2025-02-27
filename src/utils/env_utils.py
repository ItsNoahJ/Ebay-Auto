"""
Environment variable utilities.
"""
from pathlib import Path
from typing import Dict, Optional
import os
import re

def read_env_file(env_path: str = ".env") -> Dict[str, str]:
    """Read variables from .env file."""
    env_vars = {}
    
    try:
        if Path(env_path).exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"\'')
    except Exception as e:
        print(f"Error reading .env file: {e}")
        
    return env_vars

def write_env_file(env_vars: Dict[str, str], env_path: str = ".env"):
    """Write variables to .env file."""
    try:
        # Read existing content
        existing_vars = {}
        comments = []
        if Path(env_path).exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#'):
                        comments.append(line)
                    elif line:
                        key, value = line.split('=', 1)
                        existing_vars[key.strip()] = value.strip()
        
        # Update with new values
        existing_vars.update(env_vars)
        
        # Write back to file
        with open(env_path, 'w') as f:
            # Write comments first
            for comment in comments:
                f.write(f"{comment}\n")
            if comments:
                f.write("\n")
            
            # Write variables
            for key, value in existing_vars.items():
                f.write(f"{key}={value}\n")
                
    except Exception as e:
        print(f"Error writing .env file: {e}")

def get_api_keys() -> Dict[str, Optional[str]]:
    """Get API keys from environment."""
    return {
        "TMDB_API_KEY": os.getenv("TMDB_API_KEY"),
        "DISCOGS_CONSUMER_KEY": os.getenv("DISCOGS_CONSUMER_KEY"),
        "DISCOGS_CONSUMER_SECRET": os.getenv("DISCOGS_CONSUMER_SECRET")
    }

def set_api_key(key_name: str, value: str):
    """Set an API key in the environment and .env file."""
    # Update environment
    os.environ[key_name] = value
    
    # Update .env file
    env_vars = read_env_file()
    env_vars[key_name] = value
    write_env_file(env_vars)

def test_tmdb_api_key(api_key: str) -> bool:
    """Test if a TMDB API key is valid."""
    import requests
    try:
        response = requests.get(
            'https://api.themoviedb.org/3/movie/550',  # Test with Fight Club
            params={'api_key': api_key}
        )
        return response.status_code == 200
    except:
        return False

def test_discogs_keys(consumer_key: str, consumer_secret: str) -> bool:
    """Test if Discogs consumer key and secret are valid."""
    import requests
    try:
        response = requests.get(
            'https://api.discogs.com/database/search',
            params={
                'q': 'test',
                'type': 'release'
            },
            headers={
                'User-Agent': 'MediaProcessor/1.0',
                'Authorization': f'Discogs key={consumer_key}, secret={consumer_secret}'
            }
        )
        return response.status_code == 200
    except:
        return False
