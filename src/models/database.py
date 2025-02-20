"""
Database models and utilities.
"""
import os
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class MediaItem(Base):
    """Model representing a processed media item."""
    __tablename__ = 'media_items'
    
    id = Column(Integer, primary_key=True)
    
    # File info
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    media_type = Column(String)  # DVD, VHS, CD, etc.
    
    # Extracted data
    title = Column(String)
    year = Column(String)
    runtime = Column(String)
    barcode = Column(String)
    
    # OCR results
    ocr_text = Column(String)
    ocr_confidence = Column(Float)
    
    # Additional metadata
    extra_data = Column(JSON)  # Changed from 'metadata' to 'extra_data'
    
    # Debug info
    debug_images = Column(JSON)  # Paths to debug output images
    processing_log = Column(JSON)  # Log of processing steps and results
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Database:
    """Database connection and operations manager."""
    
    def __init__(self, db_path: str = "storage/media_processor.db"):
        """Initialize database connection."""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    def add_media_item(self, 
                       filename: str,
                       file_path: str,
                       media_type: Optional[str] = None,
                       extracted_data: Optional[Dict[str, Any]] = None,
                       ocr_data: Optional[Dict[str, Any]] = None,
                       metadata: Optional[Dict[str, Any]] = None,
                       debug_info: Optional[Dict[str, Any]] = None) -> MediaItem:
        """Add a new media item to the database."""
        session = self.Session()
        
        try:
            media_item = MediaItem(
                filename=filename,
                file_path=file_path,
                media_type=media_type,
                
                # Extract data if provided
                title=extracted_data.get("title") if extracted_data else None,
                year=extracted_data.get("year") if extracted_data else None,
                runtime=extracted_data.get("runtime") if extracted_data else None,
                barcode=extracted_data.get("barcode") if extracted_data else None,
                
                # OCR data if provided
                ocr_text=ocr_data.get("text") if ocr_data else None,
                ocr_confidence=ocr_data.get("confidence") if ocr_data else None,
                
                # Additional data
                extra_data=metadata or {},  # Using extra_data instead of metadata
                debug_images=debug_info.get("images", {}) if debug_info else {},
                processing_log=debug_info.get("log", []) if debug_info else []
            )
            
            session.add(media_item)
            session.commit()
            return media_item
            
        finally:
            session.close()
    
    def get_media_item(self, item_id: int) -> Optional[MediaItem]:
        """Retrieve a media item by ID."""
        session = self.Session()
        try:
            return session.query(MediaItem).filter(MediaItem.id == item_id).first()
        finally:
            session.close()
    
    def get_recent_items(self, limit: int = 10) -> list[MediaItem]:
        """Get most recently processed items."""
        session = self.Session()
        try:
            return session.query(MediaItem).order_by(
                MediaItem.created_at.desc()
            ).limit(limit).all()
        finally:
            session.close()
    
    def update_media_item(self, 
                         item_id: int, 
                         updates: Dict[str, Any]) -> Optional[MediaItem]:
        """Update a media item with new data."""
        session = self.Session()
        try:
            item = session.query(MediaItem).filter(MediaItem.id == item_id).first()
            if item:
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                session.commit()
            return item
        finally:
            session.close()
    
    def delete_media_item(self, item_id: int) -> bool:
        """Delete a media item by ID."""
        session = self.Session()
        try:
            item = session.query(MediaItem).filter(MediaItem.id == item_id).first()
            if item:
                session.delete(item)
                session.commit()
                return True
            return False
        finally:
            session.close()
