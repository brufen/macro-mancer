import pytest
from datetime import datetime, timedelta
from google.adk.agents import EvalSet, EvalCase, AgentContext
from google.adk.tools.tool_context import ToolContext
from ..agent import root_agent, process_news
from ..tools import RSSFeedTool, DatabaseTool

@pytest.fixture
def rss_tool():
    return RSSFeedTool()

@pytest.fixture
def db_tool():
    return DatabaseTool()

@pytest.fixture
def tool_context():
    return ToolContext(
        user_content=None,
        metadata={}
    )

@pytest.mark.asyncio
async def test_rss_tool(rss_tool, tool_context):
    """Test RSS feed tool functionality."""
    result = await rss_tool.run_async(
        args={},
        tool_context=tool_context
    )
    
    assert "articles" in result
    assert isinstance(result["articles"], list)
    
    if result["articles"]:
        article = result["articles"][0]
        assert "title" in article
        assert "link" in article
        assert "published" in article
        assert "summary" in article
        
        # Check if articles are within time limit
        published = datetime.fromisoformat(article["published"])
        assert published > datetime.now() - timedelta(hours=24)

@pytest.mark.asyncio
async def test_db_tool(db_tool, tool_context):
    """Test database tool functionality."""
    test_record = {
        "entity": "Test Company",
        "type": "market",
        "impact": "positive",
        "impact_description": "Test impact description"
    }
    
    result = await db_tool.run_async(
        args={"impact_record": test_record},
        tool_context=tool_context
    )
    
    assert "write_status" in result
    assert result["write_status"] in ["success", "error"]
    if result["write_status"] == "success":
        assert "record" in result
        assert result["record"] == test_record

@pytest.fixture
def eval_set():
    return EvalSet(
        name="macro_mancer_eval",
        description="Evaluation set for Macro Mancer agents",
        cases=[
            EvalCase(
                name="test_news_fetching",
                input="Fetch the latest news articles",
                expected_output={
                    "status": "success",
                    "articles_processed": True
                }
            ),
            EvalCase(
                name="test_impact_analysis",
                input="""
                Analyze this article:
                Title: Fed Raises Interest Rates
                Summary: The Federal Reserve raised interest rates by 25 basis points.
                """,
                expected_output={
                    "status": "success",
                    "impact_records_written": True
                }
            ),
            EvalCase(
                name="test_database_write",
                input="""
                Write this impact record:
                {
                    "entity": "Banking Sector",
                    "type": "regulatory",
                    "impact": "negative",
                    "impact_description": "Higher interest rates will reduce lending"
                }
                """,
                expected_output={
                    "status": "success",
                    "write_status": "success"
                }
            )
        ]
    )

@pytest.mark.asyncio
async def test_agent_evaluation(eval_set):
    """Test the complete agent system."""
    for case in eval_set.cases:
        context = AgentContext(
            input_data={"request": case.input},
            metadata={}
        )
        result = await process_news(context)
        
        assert result["status"] == "success"
        
        if case.name == "test_news_fetching":
            assert result["articles_processed"] > 0
        elif case.name == "test_impact_analysis":
            assert result["impact_records_written"] > 0
        elif case.name == "test_database_write":
            assert result["impact_records_written"] == 1

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in the agent system."""
    # Test with invalid RSS feed
    context = AgentContext(
        input_data={"request": "Fetch news from invalid feed"},
        metadata={"RSS_FEEDS": "invalid_url"}
    )
    result = await process_news(context)
    assert result["status"] == "error"
    assert "message" in result
    
    # Test with invalid database connection
    context = AgentContext(
        input_data={"request": "Write to invalid database"},
        metadata={"DATABASE_URL": "invalid_url"}
    )
    result = await process_news(context)
    assert result["status"] == "error"
    assert "message" in result 