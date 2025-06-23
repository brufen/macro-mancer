from typing import Dict, Any, List, Optional
import feedparser
import httpx
from datetime import datetime, timedelta
import os
from google.adk.tools import FunctionTool
import pandas as pd
from google.adk.tools.tool_context import ToolContext
import logging
from ..infrastructure.container import get_analysis_service, initialize_database
import json

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO)

# Initialize database on module import
try:
    initialize_database()
except Exception as e:
    logging.warning(f"Database initialization failed: {e}")

async def fetch_rss_news(*, tool_context: Optional[object] = None) -> Dict[str, Any]:
    """Fetches news articles from configured RSS feeds and returns structured data."""
    feeds = os.getenv("RSS_FEEDS", "https://finance.yahoo.com/news/rssindex").split(",")
    # max_age_hours = float(os.getenv("MAX_NEWS_AGE_HOURS", "48"))

    articles = []
    cutoff_time = get_last_update_time()

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RSSFetcher/1.0; +https://github.com/brufen/macro-mancer)",
        # ... other headers ...
    }

    async with httpx.AsyncClient() as client:
        for feed_url in feeds:
            logging.info(f"Fetching from: {feed_url}")
            try:
                response = await client.get(feed_url, headers=headers)
                response.raise_for_status()

                feed = feedparser.parse(response.text)
                logging.info(f"Found {len(feed.entries)} entries in feed")

                for entry in feed.entries:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                        logging.info(f"Article: {entry.title[:50]}... published: {published}")

                        # Optional filter
                        if published > cutoff_time:
                            articles.append({
                                "title": entry.title,
                                "summary": entry.summary,
                                "link": entry.link,
                                "published": published.isoformat(),
                                "source": feed_url
                            })
                    except Exception as e:
                        logging.error(f"Error parsing entry: {e}")
                        continue
            except Exception as e:
                logging.error(f"Error fetching feed {feed_url}: {e}")
                continue

    logging.info(f"Returning {len(articles)} articles")

    # Return structured data that can be easily processed
    return {
        "articles": articles,
        "count": len(articles),
        "sources": feeds
    }

"""dummy for potential db call"""
def get_last_update_time()->datetime:
    max_age_hours = float(os.getenv("MAX_NEWS_AGE_HOURS", "48"))
    return datetime.now() - timedelta(hours=max_age_hours)

def process_analysis(tool_context: ToolContext):
    """Process analysis results and generate recommendations."""
    try:
        session_state = tool_context.state
        analysis_result = session_state.get('analysis_result')

        if not analysis_result:
            logging.warning("No analysis_result found in session state")
            return {
                "error": "No analysis results available",
                "recommendations": [],
                "message": "Please run news analysis first"
            }

        logging.info(f"Processing analysis result: {analysis_result[:200]}...")

        # Process the analysis and generate recommendations
        df = make_recommendation(analysis_result, db_simulation=True)

        if df.empty:
            return {
                "message": "No recommendations generated",
                "recommendations": [],
                "reason": "No valid analysis data found"
            }

        # Convert DataFrame to JSON with proper error handling
        try:
            result_json = df.to_json(orient='records')
            logging.info(f"Generated recommendations: {len(df)} assets")
            return {
                "success": True,
                "recommendations": result_json,
                "count": len(df)
            }
        except Exception as e:
            logging.error(f"Error converting DataFrame to JSON: {e}")
            return {
                "error": f"Error formatting recommendations: {str(e)}",
                "recommendations": []
            }

    except Exception as e:
        logging.error(f"Error in process_analysis: {e}")
        return {
            "error": f"Processing failed: {str(e)}",
            "recommendations": []
        }


async def db_call(cut_time):
    """Real database call implementation using hexagonal architecture."""
    try:
        analysis_service = get_analysis_service()
        historical_data = await analysis_service.get_historical_data(cut_time)

        # Convert domain entities to the format expected by make_recommendation
        history_assets = []
        history_macro = []

        for analysis in historical_data:
            if analysis.type.value == 'Asset':
                history_assets.append({
                    'Ticker': analysis.entity,
                    'impact': analysis.impact,
                    'timestamp': analysis.timestamp.isoformat(),
                    'link': analysis.link or '',
                    'Summary': analysis.summary or ''
                })
            elif analysis.type.value == 'Macro':
                history_macro.append({
                    'Asset': analysis.entity,
                    'impact': analysis.impact,
                    'timestamp': analysis.timestamp.isoformat(),
                    'link': analysis.link or '',
                    'Summary': analysis.summary or ''
                })

        return history_macro, history_assets

    except Exception as e:
        logging.error(f"Database call failed: {e}")
        return [], []


def make_recommendation(input_str, db_simulation=False):
    """Generate asset recommendations from analysis data."""
    try:
        if not input_str or input_str.strip() == "":
            logging.warning("Empty input string provided to make_recommendation")
            return pd.DataFrame()

        # strip from junk
        input_str = input_str.replace('```json', '').replace('```', '').strip()

        if not input_str:
            logging.warning("Input string is empty after cleaning")
            return pd.DataFrame()

        # str to list with error handling
        try:
            l = json.loads(input_str)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in input: {e}")
            logging.error(f"Input string: {input_str[:200]}...")
            return pd.DataFrame()

        if not isinstance(l, list) or len(l) == 0:
            logging.warning("Input is not a valid list or is empty")
            return pd.DataFrame()

        # collected tables
        types = ['Tag', 'Asset', 'ScopeRelation', 'Scope', 'ScopeRelation', 'Macro', 'Location']

        # table dataframes from the input with error handling
        seprated_dfs = {}
        for type_name in types:
            try:
                type_data = [e for e in l if e.get('type') == type_name]
                seprated_dfs[type_name] = pd.DataFrame(type_data)
            except Exception as e:
                logging.error(f"Error processing type {type_name}: {e}")
                seprated_dfs[type_name] = pd.DataFrame()

        # Check if we have any data to process
        if seprated_dfs['Asset'].empty and seprated_dfs['Macro'].empty:
            logging.warning("No Asset or Macro data found in analysis")
            return pd.DataFrame()

        # Process macro data
        macro = seprated_dfs['Macro']
        if not macro.empty:
            if 'type' in macro.columns:
                macro.drop(columns=['type'], inplace=True)
            if 'timestamp' in macro.columns:
                macro['timestamp'] = pd.to_datetime(macro['timestamp'], errors='coerce')

        # Process asset data
        assets = seprated_dfs['Asset']
        if not assets.empty:
            if 'type' in assets.columns:
                assets.drop(columns=['type'], inplace=True)
            if 'timestamp' in assets.columns:
                assets['timestamp'] = pd.to_datetime(assets['timestamp'], errors='coerce')

        # Process location data
        locations = seprated_dfs['Location']
        if not locations.empty:
            if 'Scope' in locations.columns:
                locations.rename(columns={'Scope': 'Location'}, inplace=True)
            if 'type' in locations.columns:
                locations.drop(columns=['type'], inplace=True)

        # Handle case where we have no valid data
        if assets.empty and macro.empty:
            logging.warning("No valid asset or macro data after processing")
            return pd.DataFrame()

        # Get most recent timestamp
        all_timestamps = []
        if not assets.empty and 'timestamp' in assets.columns:
            all_timestamps.extend(assets['timestamp'].dropna().tolist())
        if not macro.empty and 'timestamp' in macro.columns:
            all_timestamps.extend(macro['timestamp'].dropna().tolist())

        if not all_timestamps:
            logging.warning("No valid timestamps found")
            return pd.DataFrame()

        most_recent_ts = max(all_timestamps)
        max_age_hours = float(os.getenv("MAX_NEWS_AGE_HOURS", "48"))

        if db_simulation:
            cutoff = most_recent_ts - timedelta(hours=max_age_hours / 2)

            if not assets.empty:
                actual_assets = assets.loc[assets['timestamp'] > cutoff]
                history_assets = assets.loc[assets['timestamp'] < cutoff]
            else:
                actual_assets = pd.DataFrame()
                history_assets = pd.DataFrame()

            if not macro.empty:
                actual_macro = macro.loc[macro['timestamp'] > cutoff]
                history_macro = macro.loc[macro['timestamp'] < cutoff]
            else:
                actual_macro = pd.DataFrame()
                history_macro = pd.DataFrame()
        else:
            # Use real database call
            import asyncio
            history_macro, history_assets = asyncio.run(db_call(cut_time=os.getenv()))

        # Combine data
        if not actual_assets.empty and not history_assets.empty:
            assets = pd.concat([actual_assets, history_assets]).copy()
        elif not actual_assets.empty:
            assets = actual_assets.copy()
        elif not history_assets.empty:
            assets = history_assets.copy()
        else:
            assets = pd.DataFrame()

        if not actual_macro.empty and not history_macro.empty:
            macro = pd.concat([actual_macro, history_macro]).copy()
        elif not actual_macro.empty:
            macro = actual_macro.copy()
        elif not history_macro.empty:
            macro = history_macro.copy()
        else:
            macro = pd.DataFrame()

        # Calculate weights
        if not macro.empty and 'timestamp' in macro.columns and 'impact' in macro.columns:
            macro['age'] = (most_recent_ts - macro['timestamp']).apply(lambda x: x.total_seconds() / 3600)
            macro['weight'] = (0.99 ** macro['age']) * macro['impact']

        if not assets.empty and 'timestamp' in assets.columns and 'impact' in assets.columns:
            assets['age'] = (most_recent_ts - assets['timestamp']).apply(lambda x: x.total_seconds() / 3600)
            assets['weight'] = (0.99 ** assets['age']) * assets['impact']

        # Prepare final results
        results = []

        if not assets.empty and 'Ticker' in assets.columns:
            assets_final = assets[['Ticker', 'weight', 'link', 'Summary']].copy()
            results.append(assets_final)

        if not macro.empty and not locations.empty and 'Location' in macro.columns:
            try:
                macro_final = macro.merge(locations, on='Location', how='inner')
                if not macro_final.empty and 'Asset' in macro_final.columns:
                    macro_final = macro_final[['Asset', 'weight', 'link', 'Summary']]
                    macro_final.rename(columns={'Asset': 'Ticker', 'weight': 'w_impact'}, inplace=True)
                    results.append(macro_final)
            except Exception as e:
                logging.error(f"Error merging macro and location data: {e}")

        if not results:
            logging.warning("No results generated from analysis")
            return pd.DataFrame()

        # Combine and process results
        res = pd.concat(results, ignore_index=True)
        res['reference'] = res['Summary'].astype(str) + '->' + res['link'].astype(str)

        # Group by ticker
        final_result = res.groupby('Ticker').agg({
            'weight': 'sum',
            'link': lambda x: ', '.join(x.astype(str))
        }).reset_index()

        logging.info(f"Generated recommendations for {len(final_result)} assets")
        return final_result

    except Exception as e:
        logging.error(f"Error in make_recommendation: {e}")
        return pd.DataFrame()


async def save_analysis_to_db(tool_context: ToolContext):
    """Save analysis results to database using hexagonal architecture."""
    try:
        session_state = tool_context.state
        analysis_result = session_state.get('analysis_result')

        if not analysis_result:
            return {"error": "No analysis result found in session state"}

        analysis_service = get_analysis_service()
        saved_analyses = await analysis_service.save_analysis_results(analysis_result)

        return {
            "success": True,
            "message": f"Saved {len(saved_analyses)} analysis results to database",
            "saved_count": len(saved_analyses)
        }

    except Exception as e:
        logging.error(f"Error saving analysis to database: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Create the tools using FunctionTool
rss_tool = FunctionTool(func=fetch_rss_news)
process_analysis_tool = FunctionTool(func=process_analysis)
save_analysis_tool = FunctionTool(func=save_analysis_to_db)

