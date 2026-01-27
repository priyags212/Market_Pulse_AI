import requests
from bs4 import BeautifulSoup
import json

link = "https://www.moneycontrol.com/news/business/ipo/shayona-engineering-ipo-closes-with-over-5-times-subscription-hannah-joseph-hospital-offer-fully-subscribed-on-day-2-13793213.html"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

try:
    res = requests.get(link, headers=headers, timeout=10)
    print(f"Status Code: {res.status_code}")
    soup = BeautifulSoup(res.text, "html.parser")

    print("\n--- JSON-LD Data ---")
    scripts = soup.find_all("script", type="application/ld+json")
    for s in scripts:
        print(s.string[:500] + "..." if s.string and len(s.string) > 500 else s.string)

    print("\n--- Meta Tags ---")
    for meta in soup.find_all("meta"):
        if "time" in str(meta) or "date" in str(meta) or "published" in str(meta):
            print(meta)

    print("\n--- Schedule Spans ---")
    print(soup.find_all("span", class_="article_schedule"))
    
    print("\n--- Time Tags ---")
    print(soup.find_all("time"))

except Exception as e:
    print(e)
