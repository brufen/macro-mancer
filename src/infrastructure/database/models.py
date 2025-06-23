"""
SQLAlchemy models for database persistence.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class ImpactAnalysisORM(Base):
    """SQLAlchemy model for impact analysis table."""
    __tablename__ = "impact_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    impact = Column(Float, nullable=False)
    impact_description = Column(Text)
    summary = Column(Text)
    link = Column(String(500))
    timestamp = Column(DateTime, nullable=False, index=True)
    inserted_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Indexes for better query performance
    __table_args__ = (
        Index('idx_entity_type', 'entity', 'type'),
        Index('idx_timestamp_type', 'timestamp', 'type'),
    )


class AssetRecommendationORM(Base):
    """SQLAlchemy model for asset recommendations table."""
    __tablename__ = "asset_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    weight = Column(Float, nullable=False, index=True)
    references = Column(Text)  # JSON string of references
    links = Column(Text)  # JSON string of links
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)

    # Indexes for better query performance
    __table_args__ = (
        Index('idx_ticker_weight', 'ticker', 'weight'),
        Index('idx_weight_desc', 'weight', 'created_at'),
    ) 