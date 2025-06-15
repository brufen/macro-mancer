from google.adk.agents import Deployment, AgentContext
from .agent import root_agent, process_news

deployment = Deployment(
    name="macro-mancer",
    description="Macroeconomic news analysis system",
    agent=root_agent,
    environment={
        "RSS_FEEDS": "https://seekingalpha.com/market_currents.xml",
        "MAX_NEWS_AGE_HOURS": "24",
        "DATABASE_URL": "postgresql://macro_mancer_user:password@localhost:5432/macro_mancer"
    },
    handlers={
        "process_news": process_news
    }
) 