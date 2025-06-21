import os
from datetime import datetime
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .tools import rss_tool, process_analysis
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


# TODO we should dongrade the results into list of simple dicts:
# https://github.com/google/adk-python/issues/293

ANALYSIS_PROMPT_PETER="""
You are a financial analyzer. 
When you receive a list of news article, analyze each the following ways:

In order to judge what macroeconomic event or economic trend influences the valuation of treadable assets, for each of these assets we want to know
- what asset class it belongs to (Stock, crypto, commodity, etc),
- a set of scopes or tags, that describes what is the key businesses the asset related to (For example: Elecrtic vehicles, manufacturing, retail, real estate, oil industry, etc ).
- Also we want to maintain, what geographical economic areas they operate in (global, US, Germany, European Union).
- For more general articles we also want to know what businesses and geographical areas are affected, in order to map these effects to tradeable assets.

Thus first decide whether the given article is about:

1. concrete assets(type:"Asset"),

2. asset classes or business areas(type:"Scope"),

3. some macro event (Type: "Macro").


We want to evaluate the impact of the articles on various entity types on the following scale:

-3:very negative;

-2: negative;

-1: slightly negative;

0: neutral;

1: slightly positive;

2: positive;

3: very positive.



Based on this categorisation do the followings :

1. "Asset": what kind of impact does the article has on the valuation of the mentioned assets or asset class? Also collect "tags", and location of operations. Summerize very shortly the article, and add the link of the article to the results too. Save the timestamp of the article too.

For example a single asset might have the following description:

{"type":"Asset","Summary":<summary>,"link":<link>,"Name":<Name>,"Ticker":<ticker> "tags":[<Scope1>,<Scope2>],"location":[<location1>,<location2>],"impact":<impact>,"timestamp":<timestamp> }


2. "Scope": What kind of impact does the article has on the mentined asset classes or businesses? Collect "tags", that is a list keywords, what asset class and what business areas are also affected by those asset classes or entities that are mentioned in the article. Aslo add the geographical localisation.  Save the timestamp of the article too.

{"type":"Scope","Scope":<Scope>,"Summary":<summary>,"link":<link>,"tags":[<Scope1>,<Scope2>],"location":[<location1>,<location2>],"impact":<impact>,"timestamp":<timestamp> }
}



3. "Macro": What kind of impact does the article has, what asset classes what business ares and geographical locations("tags" and "location"-s) are affected and how. Save the timestamp of the article too.

{"type":"Macro","Summary":<summary>,"link":<link>,"tags":[<Scope1>,<Scope2>],"location":[<location1>,<location2>],"impact":<impact>,"timestamp":<timestamp> }
}


If an article is about multiple entities, generate a result object for all the mentioned entities.

Concatanate the output lists of objects per categories and return them in a single json object.

 
"""

ORIG_ANALYSER_PROMPT="""
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

recommender=Agent(
    name="recommender",
    description="Agent to mock updating the database with the result of the analysis, then return the best assets",
    disallow_transfer_to_parent = True,
    instruction="When you receive an analysis object pass it to 'process_analysis' for processing and return the result. If the function fails, print out what did you pass.",
    tools = [process_analysis]

)
"""
recommender=Agent(
    name="recommender",
    description="Agent to mock reading the database and return the best assets",
    disallow_transfer_to_parent = True,
    instruction=""
)
"""

# Create the news analyzer agent
news_analyzer = Agent(
    name="news_analyzer",
    description="Analyzes individual news articles for market impact and sentiment",
    #disallow_transfer_to_parent=True,
    instruction=ANALYSIS_PROMPT_PETER
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
    2. Analyze each article for potential market impacts and write to database
    3. Recommend assets with biggest potential
    
    When asked to fetch news, transfer the request to the news_fetcher agent.
    When asked to analyze news, transfer to the news_analyzer agent.
    When asked for recommendations, after fetching and analyzing the result of the analysis news transfer to recommender agent.
    
    
    Coordinate with your sub-agents to accomplish this task.
    """,
    sub_agents=[
        news_fetcher,
        news_analyzer,
        recommender

    ]
)

# Alias for ADK eval compatibility
agent = root_agent

