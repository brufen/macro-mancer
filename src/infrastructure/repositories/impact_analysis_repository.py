"""
Concrete implementation of ImpactAnalysisRepository using SQLAlchemy.
"""
import json
import logging
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ...domain.repositories import ImpactAnalysisRepository
from ...domain.entities import ImpactAnalysis
from ..database.config import db_config
from ..database.models import ImpactAnalysisORM

logger = logging.getLogger(__name__)


class SQLAlchemyImpactAnalysisRepository(ImpactAnalysisRepository):
    """SQLAlchemy implementation of ImpactAnalysisRepository."""
    
    def _orm_to_domain(self, orm_obj: ImpactAnalysisORM) -> ImpactAnalysis:
        """Convert ORM object to domain entity."""
        return ImpactAnalysis(
            id=orm_obj.id,
            entity=orm_obj.entity,
            type=orm_obj.type,
            impact=orm_obj.impact,
            impact_description=orm_obj.impact_description,
            summary=orm_obj.summary,
            link=orm_obj.link,
            timestamp=orm_obj.timestamp,
            inserted_at=orm_obj.inserted_at,
            updated_at=orm_obj.updated_at,
        )
    
    def _domain_to_orm(self, domain_obj: ImpactAnalysis) -> ImpactAnalysisORM:
        """Convert domain entity to ORM object."""
        return ImpactAnalysisORM(
            entity=domain_obj.entity,
            type=domain_obj.type.value,
            impact=domain_obj.impact,
            impact_description=domain_obj.impact_description,
            summary=domain_obj.summary,
            link=domain_obj.link,
            timestamp=domain_obj.timestamp or datetime.utcnow(),
        )
    
    async def save(self, analysis: ImpactAnalysis) -> ImpactAnalysis:
        """Save a single impact analysis."""
        with db_config.get_session() as session:
            orm_obj = self._domain_to_orm(analysis)
            session.add(orm_obj)
            session.flush()  # Get the ID
            session.refresh(orm_obj)
            result = self._orm_to_domain(orm_obj)
            logger.info(f"Saved impact analysis for entity: {analysis.entity}")
            return result
    
    async def save_many(self, analyses: List[ImpactAnalysis]) -> List[ImpactAnalysis]:
        """Save multiple impact analyses."""
        with db_config.get_session() as session:
            orm_objects = [self._domain_to_orm(analysis) for analysis in analyses]
            session.add_all(orm_objects)
            session.flush()
            
            # Refresh all objects to get IDs
            for orm_obj in orm_objects:
                session.refresh(orm_obj)
            
            results = [self._orm_to_domain(orm_obj) for orm_obj in orm_objects]
            logger.info(f"Saved {len(analyses)} impact analyses")
            return results
    
    async def get_by_entity(self, entity: str) -> List[ImpactAnalysis]:
        """Get analyses by entity name."""
        with db_config.get_session() as session:
            orm_objects = session.query(ImpactAnalysisORM).filter(
                ImpactAnalysisORM.entity == entity
            ).order_by(desc(ImpactAnalysisORM.timestamp)).all()
            
            return [self._orm_to_domain(orm_obj) for orm_obj in orm_objects]
    
    async def get_by_type(self, type_name: str) -> List[ImpactAnalysis]:
        """Get analyses by type."""
        with db_config.get_session() as session:
            orm_objects = session.query(ImpactAnalysisORM).filter(
                ImpactAnalysisORM.type == type_name
            ).order_by(desc(ImpactAnalysisORM.timestamp)).all()
            
            return [self._orm_to_domain(orm_obj) for orm_obj in orm_objects]
    
    async def get_since(self, since: datetime) -> List[ImpactAnalysis]:
        """Get analyses created since a given time."""
        with db_config.get_session() as session:
            orm_objects = session.query(ImpactAnalysisORM).filter(
                ImpactAnalysisORM.timestamp >= since
            ).order_by(desc(ImpactAnalysisORM.timestamp)).all()
            
            return [self._orm_to_domain(orm_obj) for orm_obj in orm_objects]
    
    async def get_all(self) -> List[ImpactAnalysis]:
        """Get all analyses."""
        with db_config.get_session() as session:
            orm_objects = session.query(ImpactAnalysisORM).order_by(
                desc(ImpactAnalysisORM.timestamp)
            ).all()
            
            return [self._orm_to_domain(orm_obj) for orm_obj in orm_objects] 