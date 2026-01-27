import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import os
import concurrent.futures
import threading
from sentiment import analyze_sentiment

# CONFIG
# CONFIG
# Specific categories based on user request (Business & Markets)
# CONFIG
# Specific categories based on user request (Business & Markets)
CATEGORY_URLS = {
    # Business
    "Economy": "https://www.moneycontrol.com/news/business/economy/",
    "Companies": "https://www.moneycontrol.com/news/business/companies/",
    "Mutual Funds": "https://www.moneycontrol.com/news/business/mutual-funds/",
    "Personal Finance": "https://www.moneycontrol.com/news/business/personal-finance/",
    "IPO": "https://www.moneycontrol.com/news/business/ipo/",
    "Startup": "https://www.moneycontrol.com/news/business/startup/",
    "Real Estate": "https://www.moneycontrol.com/news/business/real-estate/",
    "Banking": "https://www.moneycontrol.com/news/business/banking/", # Added Banking
    
    # Markets
    "Stocks": "https://www.moneycontrol.com/news/business/stocks/",
    "Technical Analysis": "https://www.moneycontrol.com/news/business/markets/technical-analysis/", # Added
    "Equity Research": "https://www.moneycontrol.com/news/business/markets/equity-research/", # Added
    "Commodities": "https://www.moneycontrol.com/news/business/commodities/",
    "Currency": "https://www.moneycontrol.com/news/business/currency/",
    "Gold Rate": "https://www.moneycontrol.com/news/commodities/gold/", # Added specific gold
    "Silver Rate": "https://www.moneycontrol.com/news/commodities/silver/", # Added specific silver
    "AQI": "https://www.moneycontrol.com/news/environment/", # Best fit for AQI/Environment
    "Earnings": "https://www.moneycontrol.com/news/business/earnings/",
    
}

JSON_FILE = "moneycontrol_news.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def load_existing_news():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_news(news_list):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(news_list, f, indent=4, ensure_ascii=False)

# Global Cache for article details to avoid re-fetching
# This will be populated from existing JSON on startup
ARTICLE_CACHE = {}

def populate_cache(news_items):
    global ARTICLE_CACHE
    for item in news_items:
        if "link" in item:
            ARTICLE_CACHE[item["link"]] = {
                "image_url": item.get("image_url"),
                "timestamp": item.get("timestamp"),
                "sentiment": item.get("sentiment"),
                "sentiment_score": item.get("sentiment_score"),
                "full_content": item.get("full_content")
            }

def fetch_details_single(link, basic_data):
    """Fetches details for a single article link."""
    image_url = basic_data.get("image_url")
    timestamp = None  # Start with None instead of current time
    
    try:
         article_res = requests.get(link, headers=HEADERS, timeout=5)
         if article_res.status_code == 200:
             a_soup = BeautifulSoup(article_res.text, "html.parser")
             
             # Extract high-quality image from OG tag
             og_image = a_soup.find("meta", property="og:image")
             if og_image and og_image.get("content"):
                 image_url = og_image.get("content")

             # Try JSON-LD for data (most reliable for MoneyControl)
             scripts = a_soup.find_all("script", type="application/ld+json")
             for script in scripts:
                if script.string:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, list):
                            for item in data:
                                if "datePublished" in item and not timestamp:
                                    timestamp = item["datePublished"]
                                if "image" in item and not image_url:
                                    if isinstance(item["image"], dict) and "url" in item["image"]:
                                        image_url = item["image"]["url"]
                                    elif isinstance(item["image"], str):
                                        image_url = item["image"]
                                
                        elif isinstance(data, dict):
                            if "datePublished" in data and not timestamp:
                                timestamp = data["datePublished"]
                            if "image" in data and not image_url:
                                if isinstance(data["image"], dict) and "url" in data["image"]:
                                    image_url = data["image"]["url"]
                                elif isinstance(data["image"], str):
                                    image_url = data["image"]
                    except:
                        continue
                if timestamp:
                    break
             
             # Fallback 1: Meta tag for article published time
             if not timestamp:
                 meta_date = a_soup.find("meta", property="article:published_time")
                 if meta_date and meta_date.get("content"):
                     timestamp = meta_date.get("content")
             
             # Fallback 2: OG published time
             if not timestamp:
                 og_date = a_soup.find("meta", property="og:published_time")
                 if og_date and og_date.get("content"):
                     timestamp = og_date.get("content")
             
             # Fallback 3: Look for timestamp in article body (MoneyControl specific)
             if not timestamp:
                 # MoneyControl often has publish time in span with class "article_schedule"
                 time_span = a_soup.find("span", class_="article_schedule")
                 if time_span:
                     timestamp = time_span.get_text(strip=True)
                 else:
                     # Try to find time element
                     time_elem = a_soup.find("time")
                     if time_elem:
                         timestamp = time_elem.get("datetime") or time_elem.get_text(strip=True)

    except Exception as e:
        print(f"Error fetching article details for {link}: {e}")

    # Format timestamp
    try:
        if timestamp and isinstance(timestamp, str):
            # Try parsing ISO format (from JSON-LD)
            try:
                dt_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt_obj.strftime("%d %b %Y, %I:%M %p")
            except:
                # Try parsing other common formats
                # MoneyControl sometimes uses formats like "January 27, 2026 13:06 IST"
                for fmt in [
                    "%B %d, %Y %H:%M IST",
                    "%d %B %Y, %I:%M %p",
                    "%d %b %Y, %I:%M %p",
                    "%Y-%m-%d %H:%M:%S",
                    "%d-%m-%Y %H:%M:%S"
                ]:
                    try:
                        dt_obj = datetime.strptime(timestamp, fmt)
                        timestamp = dt_obj.strftime("%d %b %Y, %I:%M %p")
                        break
                    except:
                        continue
        
        # Only use current time if we absolutely couldn't find a timestamp
        if not timestamp:
            print(f"Warning: Could not extract timestamp for {link}, using current time")
            timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
    except Exception as e:
        print(f"Error formatting timestamp for {link}: {e}")
        timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")

    # Analyze Sentiment
    sentiment_result = {"label": "neutral", "score": 0.0}
    try:
        # Use headline for faster initial sentiment, but full_content is better if we have it
        # However, for deep_fetch, headline is already available in basic_data
        sentiment_result = analyze_sentiment(basic_data.get("headline", ""))
    except Exception as e:
        print(f"Sentiment analysis failed for {link}: {e}")

    # Fetch Full Content
    full_content = None
    try:
        full_content = scrape_article_content(link)
    except Exception as e:
        print(f"Error fetching content for {link}: {e}")

    return {
        "image_url": image_url,
        "timestamp": timestamp,
        "sentiment": sentiment_result['label'],
        "sentiment_score": sentiment_result['score'],
        "full_content": full_content
    }

def extract_listing_timestamp(article_element):
    """
    Extract timestamp from article listing element on category pages.
    MoneyControl often shows relative times or dates on listing pages.
    """
    try:
        # Look for span with time/date info
        time_span = article_element.find("span")
        if time_span:
            time_text = time_span.get_text(strip=True)
            
            # Handle relative times (e.g., "2 hours ago", "1 day ago")
            if "ago" in time_text.lower():
                from datetime import timedelta
                now = datetime.now()
                
                if "hour" in time_text.lower():
                    hours = int(''.join(filter(str.isdigit, time_text)) or 1)
                    return now - timedelta(hours=hours)
                elif "day" in time_text.lower():
                    days = int(''.join(filter(str.isdigit, time_text)) or 1)
                    return now - timedelta(days=days)
                elif "minute" in time_text.lower():
                    return now  # Recent enough
                    
            # Try to parse absolute dates
            # MoneyControl formats: "Jan 27, 2026" or "27 Jan 2026"
            for fmt in ["%b %d, %Y", "%d %b %Y", "%B %d, %Y", "%d %B %Y"]:
                try:
                    return datetime.strptime(time_text, fmt)
                except:
                    continue
                    
    except Exception as e:
        pass
    
    return None

def scrape_category(url, category_name):
    print(f"Scraping [{category_name}] Headlines...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("li", class_="clearfix")
    
    results = []
    cutoff_date = datetime.now() - timedelta(days=7)  # Only articles from last 7 days
    
    # Fast Scrape: Only get headlines and links
    for article in articles[:24]:
        title_tag = article.find("h2")
        link_tag = article.find("a")
        if not title_tag or not link_tag: continue
        
        headline = title_tag.text.strip()
        link = link_tag.get("href")
        if not link or "moneycontrol.com" not in link: continue
        
        # Try to extract preliminary timestamp from listing page
        listing_timestamp = extract_listing_timestamp(article)
        
        # Filter out old articles based on listing timestamp
        if listing_timestamp and listing_timestamp < cutoff_date:
            print(f"Skipping old article: {headline[:50]}... (Date: {listing_timestamp.strftime('%d %b %Y')})")
            continue

        # Initial minimal record
        if link in ARTICLE_CACHE and ARTICLE_CACHE[link].get("full_content"):
            cached = ARTICLE_CACHE[link]
            # Also check cached timestamp
            cached_time = cached.get("timestamp")
            if cached_time:
                try:
                    cached_dt = datetime.strptime(cached_time, "%d %b %Y, %I:%M %p")
                    if cached_dt < cutoff_date:
                        print(f"Skipping cached old article: {headline[:50]}...")
                        continue
                except:
                    pass
                    
            results.append({
                "category": category_name,
                "headline": headline,
                "link": link,
                **cached
            })
        else:
            # Placeholder for deep fetch (either brand new or missing full_content)
            results.append({
                "category": category_name,
                "headline": headline,
                "link": link,
                "image_url": ARTICLE_CACHE.get(link, {}).get("image_url"),
                "timestamp": ARTICLE_CACHE.get(link, {}).get("timestamp") or datetime.now().strftime("%d %b %Y, %I:%M %p"),
                "sentiment": ARTICLE_CACHE.get(link, {}).get("sentiment") or "neutral",
                "sentiment_score": ARTICLE_CACHE.get(link, {}).get("sentiment_score") or 0.0,
                "needs_deep_fetch": True 
            })

    return results

def deep_fetch_metadata(news_list):
    """
    Takes a list of news items and fills in missing metadata (images, real dates, sentiment) in parallel.
    """
    to_fetch = [item for item in news_list if item.get("needs_deep_fetch")]
    if not to_fetch:
        return news_list

    print(f"Starting deep fetch for {len(to_fetch)} articles...")
    
    # Limit workers to avoid overloading sentiment model/network
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(fetch_details_single, item['link'], item): item for item in to_fetch}
        
        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            try:
                details = future.result()
                # Update item in place
                item.update(details)
                item.pop("needs_deep_fetch", None)
                # Update cache
                ARTICLE_CACHE[item['link']] = details
            except Exception as e:
                print(f"Deep fetch failed for {item['link']}: {e}")
    
    return news_list

def scrape_moneycontrol():
    all_scraped_news = []
    
    # Use ThreadPoolExecutor for parallel scraping
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Create a list of futures
        future_to_category = {
            executor.submit(scrape_category, url, name): name 
            for name, url in CATEGORY_URLS.items()
        }
        
        for future in concurrent.futures.as_completed(future_to_category):
            category = future_to_category[future]
            try:
                news_items = future.result()
                if news_items:
                    all_scraped_news.extend(news_items)
            except Exception as e:
                print(f"Error scraping category {category}: {e}")
                
    return all_scraped_news

def scrape_article_content(url):
    """
    Scrapes the full text content of a news article.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Method 1: Try JSON-LD (Most reliable for Moneycontrol)
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    # JSON-LD can be a list or direct object
                    if isinstance(data, list):
                        for item in data:
                            if "articleBody" in item:
                                return item["articleBody"]
                    elif isinstance(data, dict):
                        if "articleBody" in data:
                            return data["articleBody"]
                except json.JSONDecodeError:
                    continue
        
        # Method 2: Fallback to scraping paragraphs
        # Common text containers on Moneycontrol
        content_div = soup.find("div", class_="content_wrapper") or \
                      soup.find("div", class_="arti-flow") or \
                      soup.find("div", id="article-main")
                      
        if content_div:
            # aggressive cleaning
            for tag in content_div(["script", "style", "aside", "div.ads", "div.related_news"]):
                tag.decompose()
            
            paragraphs = content_div.find_all("p")
            clean_text = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                # Filter out garbage commonly causing hallucinations
                if len(text) < 20: continue # Skip tiny fragments
                if "Read Also" in text or "Click here" in text: continue
                clean_text.append(text)
                
            return "\n".join(clean_text)

        return "Could not extract article content."

    except Exception as e:
        print(f"Error scraping article content: {e}")
        return None

def remove_duplicates(existing_news, new_news):
    existing_links = {item["link"] for item in existing_news}
    unique_news = []
    for item in new_news:
        if item["link"] not in existing_links:
            unique_news.append(item)
    return unique_news

# Global background thread lock
import threading
scrape_lock = threading.Lock()

def background_scrape_and_save(existing_news):
    if scrape_lock.locked():
        print("Scrape already in progress. Skipping.")
        return

    with scrape_lock:
        print("Starting background scrape...")
        try:
            # Phase 1: Fast Headlines Scrape
            new_scraped_news = scrape_moneycontrol()
            if new_scraped_news:
                # Phase 2: Deep Metadata Fetch (Images/Sentiment/Content)
                new_scraped_news = deep_fetch_metadata(new_scraped_news)
                
                # Merge logic: Use a map to handle duplicates and updates
                # new_scraped_news contains the freshest data (including full_content)
                merged_map = {item["link"]: item for item in existing_news}
                for item in new_scraped_news:
                    if item["link"] in merged_map:
                        # Update existing item with new details if it was missing something
                        merged_map[item["link"]].update(item)
                    else:
                        # New item
                        merged_map[item["link"]] = item
                
                # Convert back to list
                updated_news = list(merged_map.values())
                
                # Filter out articles older than 7 days
                cutoff_date = datetime.now() - timedelta(days=7)
                filtered_news = []
                for article in updated_news:
                    try:
                        timestamp_str = article.get("timestamp", "")
                        if timestamp_str:
                            article_date = datetime.strptime(timestamp_str, "%d %b %Y, %I:%M %p")
                            if article_date >= cutoff_date:
                                filtered_news.append(article)
                            else:
                                print(f"Filtering out old article: {article.get('headline', '')[:50]}... (Date: {timestamp_str})")
                    except:
                        # If we can't parse the date, keep the article to be safe
                        filtered_news.append(article)
                
                # Sort by timestamp (most recent first)
                try:
                    filtered_news.sort(key=lambda x: datetime.strptime(x.get("timestamp", ""), "%d %b %Y, %I:%M %p") if x.get("timestamp") else datetime.min, reverse=True)
                except:
                    pass

                # Keep only last 1000 items
                filtered_news = filtered_news[:1000] 
                save_news(filtered_news)
                
                # Update in-memory cache
                global NEWS_CACHE, LAST_SCRAPE_TIME
                NEWS_CACHE = filtered_news
                LAST_SCRAPE_TIME = time.time()
                
                print(f"Background scrape finished. Dataset now has {len(filtered_news)} recent articles (filtered from {len(updated_news)} total).")
            else:
                print("Background scrape finished. No articles found.")
        except Exception as e:
            print(f"Background scrape failed: {e}")

# In-memory news cache
NEWS_CACHE = []
LAST_SCRAPE_TIME = 0

def get_latest_news():
    """
    Returns data immediately. 
    If data is stale (> 5 mins), triggers a background refresh.
    If no data exists, waits for a scrape (blocking).
    """
    global NEWS_CACHE, LAST_SCRAPE_TIME
    
    # 1. Check in-memory cache first
    if NEWS_CACHE and (time.time() - LAST_SCRAPE_TIME < 300):
        return NEWS_CACHE

    # 2. Load Existing from Disk if memory cache is empty/stale
    existing_news = []
    if os.path.exists(JSON_FILE):
        existing_news = load_existing_news()
        
        # Populate Cache for faster scraping
        populate_cache(existing_news)
        
        last_modified = os.path.getmtime(JSON_FILE)
        
        # Update memory cache
        NEWS_CACHE = existing_news
        LAST_SCRAPE_TIME = last_modified

        # 300 seconds = 5 minutes cache life
        if time.time() - last_modified < 300 and existing_news: 
            return existing_news
        
        # Cache is expired, but we have data to show while updating
        if existing_news:
            print("Cache expired. Serving stale data and triggering background refresh...")
            # We already have NEWS_CACHE set
            thread = threading.Thread(target=background_scrape_and_save, args=(existing_news,))
            thread.daemon = True
            thread.start()
            return existing_news

    # 2. No Data (or empty file) - Must Block
    print("No existing data. Blocking for initial FAST scrape...")
    new_scraped_news = scrape_moneycontrol() # Only headlines
    if new_scraped_news:
        save_news(new_scraped_news)
        
        # Trigger background deep fetch for details
        print("Initial fast scrape complete. Starting background deep fetch for details...")
        thread = threading.Thread(target=background_scrape_and_save, args=(new_scraped_news,))
        thread.daemon = True
        thread.start()
        
        NEWS_CACHE = new_scraped_news
        return new_scraped_news
    
    return []

# Helper to just return raw list if needed, but get_latest_news handles logic
def get_latest_news_raw():
    return get_latest_news()

if __name__ == "__main__":
    print(get_latest_news())
