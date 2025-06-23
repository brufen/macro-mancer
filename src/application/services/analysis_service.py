"""
Analysis service - orchestrates impact analysis business logic.
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import json

from ...domain.entities import ImpactAnalysis, AssetRecommendation, AnalysisResult
from ...domain.repositories import ImpactAnalysisRepository, AssetRecommendationRepository

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for managing impact analysis operations."""
    
    def __init__(
        self,
        impact_repository: ImpactAnalysisRepository,
        recommendation_repository: AssetRecommendationRepository
    ):
        self.impact_repository = impact_repository
        self.recommendation_repository = recommendation_repository
    
    async def save_analysis_results(self, analysis_data: str) -> List[ImpactAnalysis]:
        """Save analysis results from JSON string to database."""
        try:
            # Parse the analysis data
            analyses = self._parse_analysis_data(analysis_data)
            
            # Save to database
            saved_analyses = await self.impact_repository.save_many(analyses)
            
            logger.info(f"Saved {len(saved_analyses)} analysis results")
            return saved_analyses
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            raise
    
    async def get_historical_data(self, cutoff_time: datetime) -> List[ImpactAnalysis]:
        """Get historical analysis data since cutoff time."""
        try:
            historical_data = await self.impact_repository.get_since(cutoff_time)
            logger.info(f"Retrieved {len(historical_data)} historical analyses")
            return historical_data
            
        except Exception as e:
            logger.error(f"Error retrieving historical data: {e}")
            raise
    
    async def get_asset_analyses(self, ticker: str) -> List[ImpactAnalysis]:
        """Get all analyses for a specific asset."""
        try:
            analyses = await self.impact_repository.get_by_entity(ticker)
            logger.info(f"Retrieved {len(analyses)} analyses for {ticker}")
            return analyses
            
        except Exception as e:
            logger.error(f"Error retrieving analyses for {ticker}: {e}")
            raise
    
    def _parse_analysis_data(self, analysis_data: str) -> List[ImpactAnalysis]:
        """Parse JSON analysis data into domain entities."""
        try:
            # Clean the input
            cleaned_data = analysis_data.replace('```json', '').replace('```', '').strip()
            
            # Parse JSON
            data_list = json.loads(cleaned_data)
            
            analyses = []
            for item in data_list:
                try:
                    analysis = ImpactAnalysis(
                        entity=item.get('Ticker') or item.get('Asset') or item.get('Scope', ''),
                        type=item.get('type', 'Asset'),
                        impact=float(item.get('impact', 0)),
                        impact_description=item.get('impact_description'),
                        summary=item.get('Summary', ''),
                        link=item.get('link', ''),
                        timestamp=datetime.fromisoformat(item.get('timestamp', datetime.utcnow().isoformat())),
                    )
                    analyses.append(analysis)
                except Exception as e:
                    logger.warning(f"Error parsing analysis item {item}: {e}")
                    continue
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error parsing analysis data: {e}")
            raise
    
    async def create_recommendations(self, analyses: List[ImpactAnalysis]) -> List[AssetRecommendation]:
        """Create asset recommendations from analyses."""
        try:
            # Group analyses by ticker
            ticker_analyses = {}
            for analysis in analyses:
                if analysis.type.value == 'Asset':
                    ticker = analysis.entity
                    if ticker not in ticker_analyses:
                        ticker_analyses[ticker] = []
                    ticker_analyses[ticker].append(analysis)
            
            recommendations = []
            for ticker, ticker_data in ticker_analyses.items():
                # Calculate weighted score
                total_weight = sum(analysis.impact for analysis in ticker_data)
                references = [f"{analysis.summary} -> {analysis.link}" for analysis in ticker_data]
                links = [analysis.link for analysis in ticker_data if analysis.link]
                
                recommendation = AssetRecommendation(
                    ticker=ticker,
                    weight=total_weight,
                    references=references,
                    links=links,
                    created_at=datetime.utcnow()
                )
                recommendations.append(recommendation)
            
            # Save recommendations
            if recommendations:
                saved_recommendations = await self.recommendation_repository.save_many(recommendations)
                logger.info(f"Created {len(saved_recommendations)} recommendations")
                return saved_recommendations
            
            return []
            
        except Exception as e:
            logger.error(f"Error creating recommendations: {e}")
            raise 