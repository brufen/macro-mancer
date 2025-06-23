"""
Repository interfaces - define contracts for data access.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from .entities import ImpactAnalysis, AssetRecommendation, AnalysisResult


class ImpactAnalysisRepository(ABC):
    """Repository interface for impact analysis data."""
    
    @abstractmethod
    async def save(self, analysis: ImpactAnalysis) -> ImpactAnalysis:
        """Save a single impact analysis."""
        pass
    
    @abstractmethod
    async def save_many(self, analyses: List[ImpactAnalysis]) -> List[ImpactAnalysis]:
        """Save multiple impact analyses."""
        pass
    
    @abstractmethod
    async def get_by_entity(self, entity: str) -> List[ImpactAnalysis]:
        """Get analyses by entity name."""
        pass
    
    @abstractmethod
    async def get_by_type(self, type_name: str) -> List[ImpactAnalysis]:
        """Get analyses by type."""
        pass
    
    @abstractmethod
    async def get_since(self, since: datetime) -> List[ImpactAnalysis]:
        """Get analyses created since a given time."""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[ImpactAnalysis]:
        """Get all analyses."""
        pass


class AssetRecommendationRepository(ABC):
    """Repository interface for asset recommendations."""
    
    @abstractmethod
    async def save(self, recommendation: AssetRecommendation) -> AssetRecommendation:
        """Save a single asset recommendation."""
        pass
    
    @abstractmethod
    async def save_many(self, recommendations: List[AssetRecommendation]) -> List[AssetRecommendation]:
        """Save multiple asset recommendations."""
        pass
    
    @abstractmethod
    async def get_by_ticker(self, ticker: str) -> List[AssetRecommendation]:
        """Get recommendations by ticker."""
        pass
    
    @abstractmethod
    async def get_top_recommendations(self, limit: int = 10) -> List[AssetRecommendation]:
        """Get top recommendations by weight."""
        pass
    
    @abstractmethod
    async def get_since(self, since: datetime) -> List[AssetRecommendation]:
        """Get recommendations created since a given time."""
        pass 