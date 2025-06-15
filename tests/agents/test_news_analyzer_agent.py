import json
import os
from pathlib import Path

import pytest
from unittest.mock import AsyncMock, Mock, patch

from agents.news_analyzer_agent import (
    analyze_news_content,
    process_feedback,
    news_analyzer,
    feedback_processor,
    root_agent,
)
from ml.training.model_manager import ModelPrediction


@pytest.fixture
def project_id():
    return os.getenv("GOOGLE_CLOUD_PROJECT", "macro-mancer-dev")


@pytest.fixture
def agent(project_id):
    return NewsAnalyzerAgent(project_id)


@pytest.fixture
def eval_set():
    """Create an evaluation set for testing."""
    return EvaluationSet(
        name="news_analysis_eval",
        description="Evaluation set for news analysis agent",
        examples=[
            {
                "input": "Fed raises interest rates by 25 basis points",
                "expected_output": {
                    "asset_classes": ["bonds", "stocks", "currencies"],
                    "scope": "global",
                    "confidence": 0.9,
                    "impact_score": 0.8,
                    "reasoning": "Interest rate changes have broad market impact",
                },
            },
            {
                "input": "Apple announces new iPhone with AI features",
                "expected_output": {
                    "asset_classes": ["stocks", "tech"],
                    "scope": "sector",
                    "confidence": 0.95,
                    "impact_score": 0.7,
                    "reasoning": "Product announcement affects tech sector",
                },
            },
        ],
    )


@pytest.fixture
def mock_model_manager():
    """Create a mock model manager for testing."""
    manager = Mock()
    # Use AsyncMock for async methods
    manager.analyze_news = AsyncMock(return_value=ModelPrediction(
        asset_classes=["equities", "bonds"],
        scope="global",
        confidence=0.85,
        impact_score=0.75,
        reasoning="Test reasoning",
    ))
    manager.process_feedback = AsyncMock(return_value=None)
    return manager


@pytest.mark.asyncio
async def test_analyze_news_content(mock_model_manager):
    """Test news content analysis."""
    news = "Test news content"
    result = await analyze_news_content(news, mock_model_manager)
    
    assert isinstance(result, ModelPrediction)
    assert result.asset_classes == ["equities", "bonds"]
    assert result.scope == "global"
    assert result.confidence == 0.85
    assert result.impact_score == 0.75
    assert result.reasoning == "Test reasoning"
    
    mock_model_manager.analyze_news.assert_awaited_once_with(news)


@pytest.mark.asyncio
async def test_process_feedback(mock_model_manager):
    """Test feedback processing."""
    prediction = ModelPrediction(
        asset_classes=["equities"],
        scope="local",
        confidence=0.8,
        impact_score=0.6,
        reasoning="Test prediction",
    )
    
    await process_feedback(
        prediction=prediction,
        actual_impact=0.7,
        feedback_type="impact_correction",
        comments="Test feedback",
        model_manager=mock_model_manager,
    )
    
    mock_model_manager.process_feedback.assert_awaited_once_with(
        prediction=prediction,
        actual_impact=0.7,
        feedback_type="impact_correction",
        comments="Test feedback",
    )


@pytest.mark.asyncio
async def test_news_analyzer_agent():
    """Test the news analyzer agent."""
    # Test agent configuration
    assert news_analyzer.name == "news_analyzer"
    assert news_analyzer.model == "gemini-2.0-flash"
    assert len(news_analyzer.tools) == 1
    assert news_analyzer.output_key == "news_analysis"


@pytest.mark.asyncio
async def test_feedback_processor_agent():
    """Test the feedback processor agent."""
    # Test agent configuration
    assert feedback_processor.name == "feedback_processor"
    assert feedback_processor.model == "gemini-2.0-flash"
    assert len(feedback_processor.tools) == 1
    assert feedback_processor.output_key == "feedback_analysis"


@pytest.mark.asyncio
async def test_root_agent():
    """Test the root sequential agent."""
    # Test agent configuration
    assert root_agent.name == "macro_mancer"
    assert len(root_agent.sub_agents) == 2
    assert root_agent.sub_agents[0] == news_analyzer
    assert root_agent.sub_agents[1] == feedback_processor 