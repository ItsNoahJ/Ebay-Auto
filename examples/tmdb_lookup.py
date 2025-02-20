"""
Example script demonstrating TMDB client usage with database integration.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.enrichment.tmdb_client import TMDBClient
from src.models.database import MediaItem, ProcessingResult
from src.models.db_connection import get_db

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize TMDB client
    tmdb_client = TMDBClient()
    
    # Initialize database
    db = get_db()
    db.init_db()
    
    # Example VHS titles to look up
    test_titles = [
        ("The Lion King", 1994),
        ("Jurassic Park", 1993),
        ("Back to the Future", 1985)
    ]
    
    print("Looking up movie information...")
    print("-" * 50)
    
    for title, year in test_titles:
        print(f"\nSearching for: {title} ({year})")
        
        # Search TMDB
        movie_data = tmdb_client.find_best_match(title, year)
        
        if not movie_data:
            print(f"No match found for {title}")
            continue
            
        # Create database entries
        with db.get_session() as session:
            # Create media item
            media_item = MediaItem(
                type="VHS",
                title=movie_data["title"],
                year=int(movie_data["release_date"][:4]) if movie_data.get("release_date") else None
            )
            session.add(media_item)
            session.flush()  # Get ID for foreign key
            
            # Create processing result with metadata
            result = ProcessingResult(
                media_item_id=media_item.id,
                tmdb_metadata={
                    "tmdb_id": movie_data["id"],
                    "original_title": movie_data.get("original_title"),
                    "overview": movie_data.get("overview"),
                    "poster_path": movie_data.get("poster_path"),
                    "vote_average": movie_data.get("vote_average"),
                    "runtime": movie_data.get("runtime")
                }
            )
            session.add(result)
            
        print(f"Found and saved: {movie_data['title']} ({movie_data['release_date'][:4]})")
        print(f"Overview: {movie_data.get('overview', 'N/A')[:100]}...")
        
    print("\nDone! Check the database for results.")

if __name__ == "__main__":
    main()
