import requests
from bs4 import BeautifulSoup
from newspaper import Article, ArticleException
import time
import random
import json
from datetime import datetime, timezone  # Import for datetime handling

debug_article_loc = "./scrap"

def find_key(data, target_key):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                return value
            result = find_key(value, target_key)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_key(item, target_key)
            if result is not None:
                return result
    return None


pattern = r'\b(\d+\s(?:hours?|minutes?|days?|weeks?|months?)\sago|yesterday)\b'
import re


def convert_to_timestamp(relative_time):
    now = datetime.now()

    if "minute" in relative_time:
        minutes = int(relative_time.split()[0])
        return (now - timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M:%S')

    elif "hour" in relative_time:
        hours = int(relative_time.split()[0])
        return (now - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')

    elif "yesterday" in relative_time:
        return (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

    elif "day" in relative_time:
        days = int(relative_time.split()[0])
        return (now - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    elif "week" in relative_time:
        weeks = int(relative_time.split()[0])
        return (now - timedelta(days=weeks*7)).strftime('%Y-%m-%d %H:%M:%S')
    elif "month" in relative_time:
        days = int(relative_time.split()[0])
        return (now - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    else:
        raise ValueError("Unsupported time format", relative_time)

def get_yahoo_finance_general_news_articles(num_pages=3, since_datetime=None):
    ts_list=[]
    """
    Scrapes general financial news headlines and links from Yahoo Finance,
    then attempts to download and extract the full text and metadata for each article.
    Filters articles to include only those published after a specified datetime.

    Args:
        num_pages (int): The maximum number of pages of news to scrape from Yahoo Finance.
                         Each page typically contains multiple article links.
                         Scraping might stop earlier if older articles are encountered.
        since_datetime (datetime.datetime, optional): A datetime object. Only articles
                                                     published ON or AFTER this datetime
                                                     will be returned. If None, all found
                                                     articles within num_pages are returned.

    Returns:
        list: A list of dictionaries, where each dictionary represents an article
              with keys like 'title', 'link', 'published_date', 'authors', and 'text'.
    """
    base_url = "https://finance.yahoo.com/news/"
    all_articles_data = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"--- Starting Yahoo Finance General News Article Scraper ---")
    print(f"Attempting to scrape up to {num_pages} page(s) of news.")
    if since_datetime:
        print(f"Filtering for articles published after: {since_datetime.isoformat()}")

    # Track if we've encountered an article older than since_datetime on a page
    found_old_article = False

    for i in range(num_pages):
        if found_old_article:
            print("Stopping scraping as an article older than the specified datetime was found on the previous page.")
            break

        offset = i * 25
        url = f"{base_url}?count=25&offset={offset}"

        try:
            # Step 1: Get the list of news article links from Yahoo Finance news page
            print(f"Fetching page {i + 1}/{num_pages} from {url}...")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            news_items = soup.find_all('li', class_='stream-item')  # Adjust this class if Yahoo changes its HTML

            if not news_items:
                print(f"No news items found on page {i + 1}. Stopping further scraping.")
                break

            print(f"  Found {len(news_items)} potential articles on page {i + 1}.")
            i = 0

            for item in news_items:
                link_tag = item.find('a', class_='subtle-link')
                select_result_set=item.select('div[class*="publishing"]')
                if len(select_result_set)==0:
                    print("Failed date extraction: ", item)
                    continue
                publishing_data = select_result_set[0].text.strip()
                matches = re.findall(pattern, publishing_data)
                article_published_date=convert_to_timestamp(matches[0])
                #[i.text for i in select_result_set]
                ts_list.append(publishing_data)
                if link_tag and link_tag.get('href'):
                    article_url = link_tag['href']
                    if not article_url.startswith('http'):
                        article_url = "https://finance.yahoo.com" + article_url

                    try:
                        article = Article(article_url)
                        article.download()
                        article.parse()
                        article_published_date = None
                        """
                        if article.publish_date:

                            # newspaper3k often returns timezone-naive datetimes.
                            # We make it timezone-aware (UTC) for consistent comparison.
                            # Adjust this if Yahoo Finance provides timezone info in its dates.
                            article_published_date = article.publish_date.replace(tzinfo=timezone.utc)
                            # print(f"    - Article '{article.title}' published: {article_published_date.isoformat()}")
                        else:
                            print(f"NO DATETIME: {article_url}")
                            try:

                                article_meta_data = article.meta_data
                                print("Found: ",find_key(article_meta_data,"publishDate"))


                                with open(f"{debug_article_loc}/failed_meta{i}.json", "w", encoding="utf-8") as file:
                                    json.dumps(article_meta_data)

                            except ArticleException as error:
                                print(error)

                            with open(f"{debug_article_loc}/failed{i}.html", "w", encoding="utf-8") as file:
                                file.write(article.html)
                            i += 1
                        """
                        # Check if the article is fresh enough
                        if since_datetime and article_published_date and article_published_date < since_datetime:
                            print(
                                f"    - Article '{article.title}' is too old ({article_published_date.isoformat()}). Stopping page processing.")
                            found_old_article = True  # Mark to stop outer loop
                            break  # Stop processing articles on this page

                        # Only add if it's new enough or no filter is applied
                        article_data = {
                            "title": article.title,
                            "link": article_url,
                            "published_date": str(article_published_date) if article_published_date else None,
                            "authors": article.authors,
                            "text": article.text
                        }
                        all_articles_data.append(article_data)
                        # print(f"    - Added: '{article.title}'")

                    except ArticleException as ae:
                        print(f"    - Could not process article at {article_url}: {ae}")
                    except Exception as sub_e:
                        print(f"    - An unexpected error processing {article_url}: {sub_e}")

                time.sleep(random.uniform(0.5, 1.5))  # Small delay between processing articles on a page

            print(f"Finished processing page {i + 1}.")
            time.sleep(random.uniform(2, 5))  # Polite delay between pages

        except requests.exceptions.RequestException as e:
            print(f"Error fetching Yahoo Finance news page {i + 1}: {e}")
            break
        except Exception as e:
            print(f"An unexpected error occurred while processing page {i + 1}: {e}")
            break

    print(f"--- Finished News Scraping. Total fresh articles extracted: {len(all_articles_data)} ---")
    print(ts_list)
    return all_articles_data



if __name__ == "__main__":
    print("This script is designed to be used by a Gemini Agent.")
    print("Running a test example directly...")

    # --- Test Case 1: Fetch all recent articles (e.g., last 24 hours) ---
    # To get articles from the last 24 hours:
    # 1. Get current time
    # 2. Subtract 24 hours
    # 3. Ensure it's timezone-aware (UTC is a good default for comparison)

    # Convert the current time to a datetime object in UTC
    # Current time (Monday, June 23, 2025 at 7:12:01 PM CEST)
    # Let's use a fixed current time for reproducibility for testing purposes
    # In a real agent scenario, you would use datetime.utcnow() or similar.
    # For this example, let's pretend "now" is June 23, 2025, 7 PM CEST,
    # which is 5 PM UTC (CEST is UTC+2)

    #current_utc_time = datetime(2025, 6, 23, 17, 12, 1, tzinfo=timezone.utc)
    current_utc_time = datetime.now()
    # Example: Get articles from the last 24 hours
    from datetime import timedelta
    since_24_hours_ago = current_utc_time - timedelta(hours=24)
    print(f"\n--- Testing with articles after: {since_24_hours_ago.isoformat()} ---")
    recent_articles = get_yahoo_finance_general_news_articles(num_pages=1, since_datetime=since_24_hours_ago)

    if recent_articles:
        print(f"\n--- Sample of {min(3, len(recent_articles))} Recent Articles ---")
        for i, article in enumerate(recent_articles[:3]):
            print(f"\nArticle {i+1}:")
            print(f"  Title: {article.get('title', 'N/A')}")
            print(f"  Link: {article.get('link', 'N/A')}")
            print(f"  Published Date: {article.get('published_date', 'N/A')}")
            # print(f"  Authors: {', '.join(article.get('authors', ['N/A']))}")
            # print(f"  Text (excerpt): {article.get('text', 'N/A')[:200]}...")
    else:
        print("\nNo recent articles found for the test period.")

    print("\n--- Test complete. ---")
