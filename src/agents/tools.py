from typing import Dict, Any, List, Optional
import feedparser
import httpx
from datetime import datetime, timedelta
import os
from google.adk.tools import FunctionTool
import pandas as pd
from google.adk.tools.tool_context import ToolContext


async def fetch_rss_news(*, tool_context: Optional[object] = None) -> Dict[str, Any]:
    """Fetches news articles from configured RSS feeds and returns structured data."""
    feeds = os.getenv("RSS_FEEDS", "https://finance.yahoo.com/news/rssindex").split(",")

    
    articles = []
    cutoff_time = get_last_update_time()

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

"""dummy for potential db call"""
def get_last_update_time()->datetime:
    max_age_hours = float(os.getenv("MAX_NEWS_AGE_HOURS", "48"))
    return datetime.now() - timedelta(hours=max_age_hours)

import joblib
def process_analysis(tool_context: ToolContext):
    session_state = tool_context.state
    list=session_state.get('analysis_result')
    df = make_recommendation(list,db_simulation=True)

    #joblib.dump(list,'list.pkl')

    return df.to_json(orient='records')

import json
import pandas as pd
from datetime import timedelta



def db_call(cut_time):
    pass


def make_recommendation(input_str, db_simulation=False):
    # strip from junk
    input_str = input_str.replace('```json', '').replace('```', '')
    # str to list
    l = json.loads(input_str)
    # collected tables
    types = ['Tag', 'Asset', 'ScopeRelation', 'Scope', 'ScopeRelation', 'Macro', 'Location']
    # table dataframes from the input
    seprated_dfs = {type: pd.DataFrame([e for e in l if e['type'] == type]) for type in types}
    # for  npw we only use assets, locations and macro for demontration purpose
    macro = seprated_dfs['Macro']
    macro.drop(columns=['type'], inplace=True)
    macro['timestamp'] = pd.to_datetime(macro['timestamp'])

    assets = seprated_dfs['Asset']
    assets.drop(columns=['type'], inplace=True)
    assets['timestamp'] = pd.to_datetime(assets['timestamp'])

    locations = seprated_dfs['Location']
    locations.rename(columns={'Scope': 'Location'}, inplace=True)
    locations.drop(columns=['type'], inplace=True)

    most_recent_ts = assets['timestamp'].max()
    max_age_hours = float(os.getenv("MAX_NEWS_AGE_HOURS", "48"))
    if db_simulation:
        cutoff = most_recent_ts - timedelta(hours=max_age_hours / 2)
        actual_assets = assets.loc[assets['timestamp'] > cutoff]
        history_assets = assets.loc[assets['timestamp'] < cutoff]
        actual_macro = macro.loc[macro['timestamp'] > cutoff]
        history_macro = macro.loc[macro['timestamp'] < cutoff]
        assets = actual_assets
        macro = actual_macro
    else:
        history_macro, history_assets = db_call(cut_time=os.getenv())

    assets = pd.concat([actual_assets, history_assets]).copy()
    macro = pd.concat([actual_macro, history_macro]).copy()

    macro['age'] = (most_recent_ts - macro['timestamp']).apply(lambda x: x.total_seconds() / 3600)
    macro['weight'] = (0.99 ** macro['age']) * macro['impact']

    assets['age'] = (most_recent_ts - assets['timestamp']).apply(lambda x: x.total_seconds() / 3600)
    assets['weight'] = (0.99 ** assets['age']) * assets['impact']

    assets_final = assets[['Ticker', 'weight', 'link','Summary']]

    # location decribes a localisation of the asset, this what we use as an example for proőpagation
    macro_final = macro.merge(locations, on='Location', how='inner')

    macro_final = macro_final[['Asset', 'weight', 'link','Summary']]
    macro_final.rename(columns={'Asset': 'Ticker', 'weight': 'w_impact'}, inplace=True)
    res = pd.concat([assets_final, macro_final])
    res['reference']=res['Summary']+'->'+res['link']

    return res.groupby('Ticker').agg({
        'weight': 'sum',
        'link': (lambda x: ', '.join(x))
    })


#process_analysis(input_str, db_simulation=True)

# Create the tool using FunctionTool
rss_tool = FunctionTool(func=fetch_rss_news)

