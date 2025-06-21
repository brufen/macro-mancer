import os
from datetime import datetime
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .tools import rss_tool
from typing import Dict, Any

# Create the news fetcher agent
news_fetcher = Agent(
    name="news_fetcher",
    description="Fetches and processes news articles from RSS feeds",
    tools=[rss_tool],
    output_key="articles",  # Specify the output key for the articles
    disallow_transfer_to_parent=True,  # Prevent transferring back to parent
    instruction="""
    You are a news fetching agent. 
    When you receive a request for news, ALWAYS use the fetch_rss_news tool to get the latest articles from the configured RSS feeds.
    Do not transfer to other agents - you are the expert for fetching news.
    Always call the fetch_rss_news tool and return the results to the user.
    """
)

# Create the news analyzer agent
news_analyzer = Agent(
    name="news_analyzer",
    description="Analyzes individual news articles for market impact and sentiment",
    disallow_transfer_to_parent=True,
    instruction="""
    You are a financial news analyzer agent.
    When you receive a news article, analyze it for:
    1. Market impact potential (high/medium/low)
    2. Sentiment (positive/negative/neutral)
    3. Key entities mentioned (companies, sectors, currencies)
    4. Potential trading implications
    5. Risk factors
    
    Provide a structured analysis in JSON format with these fields:
    - impact_level: high/medium/low
    - sentiment: positive/negative/neutral
    - entities: list of companies/sectors mentioned
    - trading_implications: brief analysis
    - risk_factors: any risks identified
    - confidence_score: 0-100
    """
)

# Create the root coordinator agent
root_agent = Agent(
    name="macro_mancer",
    model="gemini-2.0-flash-exp",  # Local model, no API key needed
    description="A system for analyzing macroeconomic news and its market impact",
    instruction=f"""
    You are a Macroeconomic News Analysis System.
    Today's date: {datetime.now().strftime('%Y-%m-%d')}
    
    Your task is to:
    1. Fetch recent news articles from configured RSS feeds
    2. Analyze each article for potential market impacts
    3. Store the impact analysis in the database
    
    When asked to fetch news, transfer the request to the news_fetcher agent.
    When asked to analyze news, transfer to the news_analyzer agent.
    Coordinate with your sub-agents to accomplish this task.
    """,
    sub_agents=[
        news_fetcher,
        news_analyzer,
    ]
)

# Alias for ADK eval compatibility
agent = root_agent

