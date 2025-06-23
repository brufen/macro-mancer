"""
Dependency injection container for hexagonal architecture.
"""
from typing import Optional
from .database.config import db_config
from .repositories.impact_analysis_repository import SQLAlchemyImpactAnalysisRepository
from ..application.services.analysis_service import AnalysisService

# Global instances
_impact_repository: Optional[SQLAlchemyImpactAnalysisRepository] = None
_analysis_service: Optional[AnalysisService] = None


def get_impact_repository() -> SQLAlchemyImpactAnalysisRepository:
    """Get or create the impact analysis repository instance."""
    global _impact_repository
    if _impact_repository is None:
        _impact_repository = SQLAlchemyImpactAnalysisRepository()
    return _impact_repository


def get_analysis_service() -> AnalysisService:
    """Get or create the analysis service instance."""
    global _analysis_service
    if _analysis_service is None:
        impact_repo = get_impact_repository()
        # For now, we'll use None for recommendation repo until implemented
        _analysis_service = AnalysisService(impact_repo, None)
    return _analysis_service


def initialize_database():
    """Initialize the database and create tables."""
    db_config.create_tables()


def reset_container():
    """Reset the container (useful for testing)."""
    global _impact_repository, _analysis_service
    _impact_repository = None
    _analysis_service = None 