
import requests
from bs4 import BeautifulSoup

def get_live_price(symbol):
    """
    Scrapes the live price from Google Finance as a fallback when yfinance is stale.
    Returns the price as a float, or None if failed.
    """
    # Map common symbols to Google Finance format
    # TATASTEEL.NS -> TATASTEEL:NSE
    # ^NSEI -> NIFTY_50:INDEXNSE
    # ^BSESN -> SENSEX:INDEXBOM
    
    ticker = symbol.replace(".NS", "").replace("^", "")
    exchange = "NSE"
    
    if symbol == "^NSEI":
        ticker = "NIFTY_50"
        exchange = "INDEXNSE"
    elif symbol == "^BSESN":
        ticker = "SENSEX"
        exchange = "INDEXBOM"
    elif symbol.endswith(".NS"):
        exchange = "NSE"
    elif symbol.endswith(".BO"):
        exchange = "BOM"
        ticker = symbol.replace(".BO", "")
    
    url = f"https://www.google.com/finance/quote/{ticker}:{exchange}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Current Price class usually "YMlKec fxKbKc"
        # Search for the main price element
        price_div = soup.find("div", class_="YMlKec fxKbKc")
        
        # Fallback for some indices or different layouts
        if not price_div:
            price_div = soup.find("div", class_="YMlKec")
            
        if price_div:
            price_text = price_div.text.replace("₹", "").replace(",", "").strip()
            return float(price_text)
            
        return None
            
    except Exception as e:
        print(f"Scraper Error for {symbol}: {e}")
        return None
