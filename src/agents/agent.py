import os
from datetime import datetime
from google.adk.agents import Agent, LlmAgent, AgentContext
from google.adk.types import GenerateContentConfig
from .tools import RSSFeedTool, DatabaseTool
from typing import Dict, Any

# Create tools
rss_tool = RSSFeedTool()
db_tool = DatabaseTool()

# Create the news fetcher agent
news_fetcher = Agent(
    name="news_fetcher",
    description="Fetches and processes news articles from RSS feeds",
    tools=[rss_tool],
    output_key="articles"  # Specify the output key for the articles
)

# Create the analyzer agent
analyzer = LlmAgent(
    name="analyzer",
    model="gemini-pro",
    description="Analyzes news articles for market impact",
    instruction="""
    Analyze the provided news article and identify potential impacts on entities.
    For each impact, provide:
    1. Entity: The company, sector, or market affected
    2. Type: The type of impact (e.g., regulatory, market, operational)
    3. Impact: One of ['strong positive', 'positive', 'strong negative', 'negative']
    4. Impact Description: A brief explanation of the impact
    
    Format the response as a JSON array of objects with these fields.
    """,
    generate_content_config=GenerateContentConfig(temperature=0.2)
)

# Create the database writer agent
db_writer = Agent(
    name="db_writer",
    description="Writes impact records to the database",
    tools=[db_tool],
    output_key="write_status"
)

# Create the root coordinator agent
root_agent = Agent(
    name="macro_mancer",
    model="gemini-pro",
    description="A system for analyzing macroeconomic news and its market impact",
    instruction=f"""
    You are a Macroeconomic News Analysis System.
    Today's date: {datetime.now().strftime('%Y-%m-%d')}
    
    Your task is to:
    1. Fetch recent news articles from configured RSS feeds
    2. Analyze each article for potential market impacts
    3. Store the impact analysis in the database
    
    Coordinate with your sub-agents to accomplish this task.
    """,
    sub_agents=[
        news_fetcher,
        analyzer,
        db_writer
    ],
    generate_content_config=GenerateContentConfig(temperature=0.1)
)

async def process_news(context: AgentContext) -> Dict[str, Any]:
    """Process news articles through the agent system."""
    # Fetch news
    news_context = AgentContext(input_data={}, metadata=context.metadata)
    news_result = await news_fetcher.process(news_context)
    
    if not news_result.get("articles"):
        return {"status": "error", "message": "No articles found"}
    
    # Process each article
    impact_records = []
    for article in news_result["articles"]:
        # Analyze article
        analysis_context = AgentContext(
            input_data={"article": article},
            metadata=context.metadata
        )
        analysis_result = await analyzer.process(analysis_context)
        
        if analysis_result.get("impact_records"):
            # Write to database
            for record in analysis_result["impact_records"]:
                db_context = AgentContext(
                    input_data={"impact_record": record},
                    metadata=context.metadata
                )
                db_result = await db_writer.process(db_context)
                if db_result.get("write_status") == "success":
                    impact_records.append(record)
    
    return {
        "status": "success",
        "articles_processed": len(news_result["articles"]),
        "impact_records_written": len(impact_records)
    } 