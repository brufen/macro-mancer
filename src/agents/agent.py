import os
from datetime import datetime

from google.adk import Runner
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import google_search

from google.adk.sessions import InMemorySessionService

from .tools import rss_tool, process_analysis,get_last_update_time
from typing import Dict, Any
GEMINI_MODEL= "gemini-2.0-flash-exp"

NEWS_FETCHER_PROMPT="""
    You are a news fetching agent. 
    Your ONLY task is, when you receive a request for news, ALWAYS use the fetch_rss_news tool to get the latest articles from the configured RSS feeds.
    """

ORIG_NEWS_FETCHER_PROMPT="""
    You are a news fetching agent. 
    Your ONLY task is, when you receive a request for news, ALWAYS use the fetch_rss_news tool first to get the latest articles from the configured RSS feeds. If you dont get any news from there, try to pull news using Google Search, that are posted after the cutoff time given by 'get_last_update_time' tool.
    Do not transfer to other agents - you are the expert for fetching news.
    """

# Create the news fetcher agent
news_fetcher = Agent(
    name="news_fetcher",
    model=GEMINI_MODEL,
    description="Fetches and processes news articles from RSS feeds",
    tools=[rss_tool],
    output_key="articles",  # Specify the output key for the articles
    disallow_transfer_to_parent=True,  # Prevent transferring back to parent
    instruction=NEWS_FETCHER_PROMPT
)



# TODO we should dongrade the results into list of simple dicts:
# https://github.com/google/adk-python/issues/293

ANALYSIS_PROMPT_PETER="""
You are a financial analyzer. 
When you receive news articles, your ONLY task is to analyze each the following ways:

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

1. "Asset": what kind of impact does the article has on the valuation of the mentioned assets?ion of operations. Summerize very shortly the article, and add the link of the article to the results too. Save the timestamp of the article too.

For example a single asset might have the following description:

{"type":"Asset","Summary":<summary>,"link":<link>,"Name":<Name>,"Ticker":<ticker>,"impact":<impact>,"timestamp":<timestamp> }

Also collect "tags", for the mentioned assets, that desrcibes what businesses they operate on on the valuation of the mentioned assets.
[{"type":"Tag", "Asset":<Ticker>,"Scope":<Scope1> },
{"type":"Tag", "Asset":<Ticker>,"Scope":<Scope2> },
{"type":"Tag", "Asset":<Ticker>,"Scope":<Scope3> }]

Also collect "locations", that are relevant to the asset:
[{"type":"Location", "Asset":<Ticker>,"Scope":<Location1> },
{"type":"Location", "Asset":<Ticker>,"Scope":<Location2> }]



2. "Scope": What kind of impact does the article has on the mentioned asset classes or businesses?  Also add the geographical localisation.  Save the timestamp of the article too.

{"type":"Scope","Scope":<Scope>,"Summary":<summary>,"link":<link>,"location":<location1>,"impact":<impact>,"timestamp":<timestamp> }

If the mentioned scopes are strongly connected other business areas create entities as follows:
{"type":"ScopeRelation","Scope1":<Scope>,"Scope2",<Scope2>},


3. "Macro": What kind of impact does the article has, what asset classes what business areas and geographical locations("tags" and "location"-s) are affected and how. Create separate entry for each of the tags pairs of tags and  locations.  Save the timestamp of the article too.

[{"type":"Macro","Summary":<summary>,"link":<link>,"Scope":<Scope1>,"Location":<location1>,"impact":<impact>,"timestamp":<timestamp> },
{"type":"Macro","Summary":<summary>,"link":<link>,"Scope":<Scope2>,"Location":<location1>,"impact":<impact>,"timestamp":<timestamp> },
...
]



If an article is about multiple entities, generate a result object for all the mentioned entities.

Concatanate all the output lists into a single output list, and save it into the session state under the key 'analysis_result'. 

 
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
    model=GEMINI_MODEL,
    description="Agent to recommend assets",
    disallow_transfer_to_parent = True,
    #instruction="YourPass information provided in the session state under the key 'analyis_result' to 'process_analysis' tool. nad return the output of that function.",
    instruction="You are a financial asset recommender agent. Your ONLY task is to give recommendation after always call 'process_analysis' tool. The tool return a list of json objects, where 'Ticker' contains the ticker of assets, 'weight' describes a score for potential of the asset, and link contains links to the interesting articles. Make recommendation based on this table. Pick assets based the highest scores, and add links from the objects as refernce."  ,
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
    model=GEMINI_MODEL,
    description="Analyzes individual news articles for market impact and sentiment",
    #disallow_transfer_to_parent=True,
    output_key='analysis_result',
    instruction=ANALYSIS_PROMPT_PETER
)

# Create the root coordinator agent
'''
root_agent = Agent(
    name="macro_mancer",
    model="gemini-2.0-flash-exp",  # Local model, no API key needed
    description="A system for analyzing macroeconomic news and its market impact",
    instruction=f"""
    You are a Macroeconomic News Analysis System.
    Today's date: {datetime.now().strftime('%Y-%m-%d')}
    
    Your task is ONLY task is to  to do one of the followings:
    1. Fetch recent news articles from configured RSS feeds
    2. Analyze each article for potential market impacts and write to database
    3. Recommend financial assets to buy, based on the latest news articles
    
    For each of the tasks, you must have executed the previous tasks.
    
    
    
    When asked to fetch news, transfer the request to the news_fetcher agent.
    When asked to analyze news, if it did not happen yet, donwload the new using 'news_fetcher' agent, then transfer to the news_analyzer agent.
    When asked to give recommendations run 'news_fetcher' and 'news_analyzer' agent, if it did not happen happen yet, then transfer to 'recommender' agent
    
    
    Coordinate with your sub-agents to accomplish this task.
    """,
    sub_agents=[
        news_fetcher,
        news_analyzer,
        recommender
    ]
)
'''

root_agent = SequentialAgent(
    name="CodePipelineAgent",
    sub_agents=[news_fetcher, news_analyzer, recommender]
)

#Could you please recommend me some financial assets based on the latest news?

