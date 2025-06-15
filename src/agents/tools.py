from typing import Dict, Any, List, Optional
import feedparser
from datetime import datetime, timedelta
import os
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext
from mcp_toolbox import DatabaseClient

class RSSFeedTool(BaseTool):
    """Tool to fetch news from RSS feeds."""
    
    def __init__(self):
        super().__init__(
            name="fetch_rss_news",
            description="Fetches news articles from configured RSS feeds"
        )
        self.feeds = os.getenv("RSS_FEEDS", "https://seekingalpha.com/market_currents.xml").split(",")
        self.max_age_hours = int(os.getenv("MAX_NEWS_AGE_HOURS", "24"))

    async def run_async(
        self, 
        *, 
        args: Dict[str, Any], 
        tool_context: Optional[ToolContext]
    ) -> Dict[str, Any]:
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)

        for feed_url in self.feeds:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                published = datetime(*entry.published_parsed[:6])
                
                if published < cutoff_time:
                    continue
                
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": published.isoformat(),
                    "summary": entry.summary
                })

        return {"articles": articles}

class DatabaseTool(BaseTool):
    """Tool to interact with the database using MCP toolbox."""
    
    def __init__(self):
        super().__init__(
            name="write_impact_record",
            description="Writes impact records to the database"
        )
        self.db_client = DatabaseClient(
            connection_string=os.getenv("DATABASE_URL")
        )

    async def run_async(
        self, 
        *, 
        args: Dict[str, Any], 
        tool_context: Optional[ToolContext]
    ) -> Dict[str, Any]:
        record = args["impact_record"]
        
        try:
            await self.db_client.execute(
                """
                INSERT INTO impact (entity, type, impact, impact_description)
                VALUES (:entity, :type, :impact, :impact_description)
                """,
                record
            )
            return {"write_status": "success", "record": record}
        except Exception as e:
            return {"write_status": "error", "error": str(e)} 