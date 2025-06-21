from typing import Dict, Any, List, Optional
import feedparser
import httpx
from datetime import datetime, timedelta
import os
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

async def fetch_rss_news(*, tool_context: Optional[object] = None) -> Dict[str, Any]:
    """Fetches news articles from configured RSS feeds and returns structured data."""
    feeds = os.getenv("RSS_FEEDS", "https://finance.yahoo.com/news/rssindex").split(",")
    max_age_hours = float(os.getenv("MAX_NEWS_AGE_HOURS", "48"))
    
    articles = []
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RSSFetcher/1.0; +https://yourdomain.com)"
    }

    async with httpx.AsyncClient() as client:
        for feed_url in feeds:
            try:
                print(f"Fetching from: {feed_url}")
                response = await client.get(feed_url, headers=headers)
                response.raise_for_status()
                
                feed = feedparser.parse(response.text)
                print(f"Found {len(feed.entries)} entries in feed")
                
                for entry in feed.entries:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                        print(f"Article: {entry.title[:50]}... published: {published}")
                        
                        # Optional filter
                        if published < cutoff_time:
                            continue
                        
                        # Get summary safely - some RSS feeds don't have summary
                        summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '') or 'No summary available'
                        
                        articles.append({
                            "title": entry.title,
                            "link": entry.link,
                            "published": published.isoformat(),
                            "summary": summary,
                            "source": "Yahoo Finance",
                            "id": f"article_{len(articles) + 1}"
                        })
                    except Exception as e:
                        print(f"Error parsing entry: {e}")
                        continue
            except Exception as e:
                print(f"Error fetching feed {feed_url}: {e}")
                continue

    print(f"Returning {len(articles)} articles")
    
    # Return structured data that can be easily processed
    return {
        "articles": articles,
        "total_count": len(articles),
        "source": "Yahoo Finance RSS",
        "fetched_at": datetime.now().isoformat(),
        "format": "structured_list"
    }

# Create the tool using FunctionTool
rss_tool = FunctionTool(func=fetch_rss_news)

