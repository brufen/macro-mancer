"""
Domain entities - core business objects using Pydantic for validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ImpactType(str, Enum):
    """Types of impact analysis."""
    ASSET = "Asset"
    SCOPE = "Scope"
    MACRO = "Macro"
    TAG = "Tag"
    LOCATION = "Location"
    SCOPE_RELATION = "ScopeRelation"


class ImpactAnalysis(BaseModel):
    """Core domain entity for impact analysis."""
    id: Optional[int] = None
    entity: str = Field(..., description="Entity name or ticker")
    type: ImpactType = Field(..., description="Type of impact")
    impact: float = Field(..., ge=-3, le=3, description="Impact score from -3 to 3")
    impact_description: Optional[str] = Field(None, description="Description of the impact")
    summary: Optional[str] = Field(None, description="Article summary")
    link: Optional[str] = Field(None, description="Source article link")
    timestamp: Optional[datetime] = Field(None, description="When the analysis was created")
    inserted_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssetRecommendation(BaseModel):
    """Domain entity for asset recommendations."""
    ticker: str = Field(..., description="Asset ticker symbol")
    weight: float = Field(..., description="Recommendation weight/score")
    references: List[str] = Field(default_factory=list, description="Source references")
    links: List[str] = Field(default_factory=list, description="Source article links")
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    """Container for multiple impact analyses."""
    analyses: List[ImpactAnalysis] = Field(default_factory=list)
    recommendations: List[AssetRecommendation] = Field(default_factory=list)
    created_at: Optional[datetime] = None 