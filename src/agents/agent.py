from google.adk.agents import Agent, SequentialAgent
from .tools import rss_tool, process_analysis_tool, save_analysis_tool
from .prompt import (
    NEWS_FETCHER_PROMPT,
    ANALYSIS_PROMPT,
    RECOMMENDER_PROMPT,
    SAVER_PROMPT
)
GEMINI_MODEL= "gemini-2.0-flash-exp"

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

recommender=Agent(
    name="recommender",
    model=GEMINI_MODEL,
    description="Agent to recommend assets",
    disallow_transfer_to_parent = True,
    instruction=RECOMMENDER_PROMPT,
    tools = [process_analysis_tool]
)

# Create the news analyzer agent
news_analyzer = Agent(
    name="news_analyzer",
    model=GEMINI_MODEL,
    description="Analyzes individual news articles for market impact and sentiment",
    output_key='analysis_result',
    instruction=ANALYSIS_PROMPT
)

# Create a database saver agent (new!)
db_saver = Agent(
    name="db_saver",
    model=GEMINI_MODEL,
    description="Saves analysis results to database",
    disallow_transfer_to_parent=True,
    instruction=SAVER_PROMPT,
    tools=[save_analysis_tool]
)

# Create the root coordinator agent
root_agent = SequentialAgent(
    name="MacroMancerAgent",
    sub_agents=[news_fetcher, news_analyzer, db_saver, recommender]
)


