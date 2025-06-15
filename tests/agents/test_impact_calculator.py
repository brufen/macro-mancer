import pytest
from datetime import datetime

from macro_mancer.models.impact import AssetImpact, ImpactScope


@pytest.mark.asyncio
async def test_calculate_impact(impact_calculator):
    """Test impact calculation."""
    # Test news content
    news_content = """
    Federal Reserve raises interest rates by 25 basis points.
    The central bank cited persistent inflation as the main reason for the hike.
    Markets reacted with increased volatility in bond and currency markets.
    """
    
    # Calculate impact
    impacts = await impact_calculator.calculate_impact(news_content)
    
    # Verify results
    assert len(impacts) > 0
    for impact in impacts:
        assert isinstance(impact, AssetImpact)
        assert impact.timestamp <= datetime.utcnow()
        assert impact.impact_score >= 0.0
        assert impact.impact_score <= 1.0
        assert impact.confidence >= 0.0
        assert impact.confidence <= 1.0
        assert impact.scope in [s.value for s in ImpactScope]
        assert impact.reasoning


@pytest.mark.asyncio
async def test_process_feedback(impact_calculator):
    """Test feedback processing."""
    # Create test prediction
    prediction = ModelPrediction(
        asset_classes=["bonds", "currencies"],
        scope="global",
        confidence=0.9,
        impact_score=0.8,
        reasoning="Interest rate changes affect global markets",
    )
    
    # Process feedback
    await impact_calculator.process_feedback(
        prediction=prediction,
        actual_impact=0.7,
        feedback_type="impact_score",
        comments="Impact was slightly lower than predicted",
    )
    
    # TODO: Add assertions to verify feedback was stored in BigQuery


@pytest.mark.asyncio
async def test_bigquery_integration(impact_calculator, bigquery_client):
    """Test BigQuery integration."""
    # Test news content
    news_content = "Test news content for BigQuery integration"
    
    # Calculate impact
    impacts = await impact_calculator.calculate_impact(news_content)
    
    # Verify data in BigQuery
    query = f"""
    SELECT *
    FROM `{impact_calculator.project_id}.{impact_calculator.dataset_id}.{impact_calculator.table_id}`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
    """
    
    query_job = bigquery_client.query(query)
    results = list(query_job)
    
    assert len(results) > 0
    for row in results:
        assert row.asset_class
        assert 0.0 <= row.impact_score <= 1.0
        assert 0.0 <= row.confidence <= 1.0
        assert row.scope
        assert row.reasoning 