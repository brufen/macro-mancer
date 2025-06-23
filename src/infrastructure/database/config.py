"""
Database configuration and connection management.
"""
import os
import logging
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration manager."""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables."""
        # For local development
        if os.getenv("DATABASE_URL"):
            return os.getenv("DATABASE_URL")
        
        # For GCP Cloud SQL
        db_user = os.getenv("DB_USER", "macro_mancer_user")
        db_password = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "macro_mancer")
        
        # Handle GCP connection string format
        if ":" in db_host and "europe-west3" in db_host:
            # This is a GCP connection string, use the primary IP address
            logger.info("Detected GCP connection string, using primary IP address")
            db_host = "34.89.182.112"  # Primary IP from GCP instance
        
        # URL-encode the password to handle special characters
        encoded_password = urllib.parse.quote_plus(db_password)
        
        logger.info(f"Connecting to database: {db_host}:{db_port}/{db_name}")
        
        return f"postgresql+psycopg2://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
    
    def _create_engine(self):
        """Create SQLAlchemy engine with connection pooling."""
        return create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables in the database."""
        from .models import Base
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")


# Global database config instance
db_config = DatabaseConfig() 