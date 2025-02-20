"""
Database initialization script.
Creates the SQLite database and required tables.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.models.database import init_db
from src.models.db_connection import get_db

def main():
    """Initialize the database and tables."""
    try:
        # Initialize tables
        print("\nInitializing database tables...")
        db = get_db()
        db.init_db()
        print("Tables created successfully!")
        
        # Test connection
        if db.check_connection():
            print("\nDatabase connection test successful!")
        else:
            print("\nWarning: Database connection test failed!")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
