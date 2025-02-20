"""
Database connection management for the VHS processing system.
"""
import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus

from .database import Base

class DatabaseConnection:
    """
    Manages database connections and provides session handling.
    """
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._init_connection()
        
    def _init_connection(self):
        """Initialize database connection using environment variables."""
        # Use SQLite database
        db_path = os.path.join(os.getcwd(), 'storage', 'database', 'vhs_processor.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        db_url = f"sqlite:///{db_path}"
        
        # Create engine and session factory
        self.engine = create_engine(
            db_url,
            echo=os.getenv('SQL_ECHO', 'false').lower() == 'true',
            pool_pre_ping=True
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
    def init_db(self):
        """Initialize database tables."""
        Base.metadata.create_all(bind=self.engine)
        
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session using context manager.
        
        Yields:
            Session: Database session
            
        Example:
            with db.get_session() as session:
                results = session.query(MediaItem).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def check_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.get_session() as session:
                # Use SQLAlchemy text() construct for the test query
                session.execute(text("SELECT 1 AS test"))
            return True
        except SQLAlchemyError:
            return False

# Create global database instance
db = DatabaseConnection()

def get_db() -> DatabaseConnection:
    """
    Get database connection instance.
    
    Returns:
        DatabaseConnection: Global database connection instance
    """
    return db
