from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import os
import json
import logging
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Import our modules
from scraper import get_latest_news
from sentiment import init_model as init_sentiment
from market_data import get_market_data, get_stock_details, get_stock_history, get_stock_financials
from chatbot import get_chat_response, init_gemini
from database import init_db, get_db, User, WatchlistItem, NewsAnalytics, hash_password, verify_password

# Scheduler & Notifications
from apscheduler.schedulers.background import BackgroundScheduler
from notification_manager import NotificationManager

# Global Scheduler
scheduler = BackgroundScheduler()
notification_manager = None

def run_notification_job():
    print("Executing scheduled notification job...")
    if notification_manager:
        notification_manager.check_and_notify()

# Load env vars
load_dotenv()

app = FastAPI(title="MarketPulse AI Backend")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

class UserSignup(BaseModel):
    name: str
    email: str
    password: str
    dob: str = None

class UserLogin(BaseModel):
    email: str
    password: str

class WatchlistRequest(BaseModel):
    email: str
    symbol: str
    name: str = None

# Fallback list of major companies
DEFAULT_STOCKS = [
    {"name": "Reliance Industries Ltd", "symbol": "RELIANCE"},
    {"name": "HDFC Bank Ltd", "symbol": "HDFCBANK"},
    {"name": "Infosys Ltd", "symbol": "INFY"},
    {"name": "Tata Consultancy Services Ltd", "symbol": "TCS"},
    {"name": "ICICI Bank Ltd", "symbol": "ICICIBANK"},
]

def load_stocks():
    global NSE_STOCKS
    try:
        stocks_path = os.path.join(os.path.dirname(__file__), "stocks.json")
        if os.path.exists(stocks_path):
            with open(stocks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Handle both list format and the new nested dict format
                if isinstance(data, dict) and "companies" in data:
                    NSE_STOCKS = list(data["companies"].values())
                elif isinstance(data, list):
                    NSE_STOCKS = data
                else:
                    NSE_STOCKS = DEFAULT_STOCKS
                
                # Cleanup and validate: Ensure each stock has 'name' and 'symbol'
                valid_stocks = []
                for s in NSE_STOCKS:
                    if isinstance(s, dict) and "name" in s and "symbol" in s:
                        valid_stocks.append(s)
                NSE_STOCKS = valid_stocks
                print(f"Successfully loaded {len(NSE_STOCKS)} valid stocks from stocks.json")
        else:
            print("Warning: stocks.json not found, using default list.")
            NSE_STOCKS = DEFAULT_STOCKS
    except Exception as e:
        print(f"Error loading stocks.json: {e}")
        NSE_STOCKS = DEFAULT_STOCKS

NSE_STOCKS = []
# Initial load
load_stocks()

import asyncio

async def load_models_background():
    print("Starting background model loading...")
    # These are synchronous, so they will block the thread they run on.
    # To be truly non-blocking for the event loop, we should run them in an executor if possible,
    # but asyncio.create_task with standard calls will still block the loop during execution of that function 
    # unless we wrap in to_thread (Python 3.9+).
    await asyncio.to_thread(init_sentiment)
    await asyncio.to_thread(init_gemini)

    print("All models loaded in background.")

@app.on_event("startup")
async def startup_event():
    print("Server starting specific tasks...")
    init_db()
    
    # Initialize Notification Manager
    global notification_manager
    from database import SessionLocal
    notification_manager = NotificationManager(SessionLocal)
    
    # Start Scheduler
    try:
        if not scheduler.running:
            scheduler.add_job(run_notification_job, 'interval', minutes=1)
            scheduler.start()
            print("Notification scheduler started (1 min interval).")
    except Exception as e:
        print(f"Error starting scheduler: {e}")

    # Offload heavy lifting to background thread
    asyncio.create_task(load_models_background())
    print("Server startup sequence complete (Models loading in background).")

@app.on_event("shutdown")
def shutdown_event():
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler shut down.")

@app.get("/")
def read_root():
    return {"message": "Welcome to MarketPulse AI API"}

def get_paginated_news(db: Session, page: int, limit: int):
    offset = (page - 1) * limit
    total_count = db.query(NewsItem).count()
    news_items = db.query(NewsItem).order_by(NewsItem.timestamp.desc()).offset(offset).limit(limit).all()
    
    return {
        "items": news_items,
        "total": total_count,
        "page": page,
        "pages": (total_count + limit - 1) // limit
    }

@app.get("/news")
def read_news(
    page: int = 1, 
    limit: int = 24, 
    q: str = None, 
    categories: str = None, 
    stocks: str = None,
    filter_type: str = None,
    db: Session = Depends(get_db)
):

    try:
        all_news = get_latest_news() 
        if not all_news:
            return {"items": [], "total": 0, "page": page, "pages": 1}

        # 0. Inject Views from Database
        # Optimization: Only fetch views for links in current dataset (or all if dataset is small enough)
        # For simplicity with sorting, we need views for ALL items first.
        try:
            analytics = db.query(NewsAnalytics).all()
            views_map = {item.news_link: item.views for item in analytics}
            
            # Update all_news with views
            for item in all_news:
                item["views"] = views_map.get(item["link"], 0)
        except Exception as e:
            print(f"Error merging views: {e}")
            # Continue without views if DB fails, defaulting to 0


        # 1. Apply Filters before sorting/pagination
        
        # Category Filter
        if categories:
            cat_list = [c.strip().lower() for c in categories.split(",") if c.strip()]
            if cat_list:
                all_news = [item for item in all_news if str(item.get("category") or "").lower() in cat_list]

        # Stock/Watchlist Filter (Strict Headline Match)
        if stocks:
            import re
            requested_symbols = {s.strip().lower() for s in stocks.split(",") if s.strip()}
            if requested_symbols:
                # Build a set of keywords (Names, Aliases, Symbols) for the requested stocks
                # Optimization: In a real app, this mapping should be pre-computed.
                target_keywords = set()
                
                # Add the symbols themselves first
                for s in requested_symbols:
                    target_keywords.add(s)

                # Look up rich data from NSE_STOCKS global
                for stock_obj in NSE_STOCKS:
                    if stock_obj.get('symbol', '').lower() in requested_symbols:
                        # Add Company Name
                        if stock_obj.get('name'):
                            name_clean = stock_obj['name'].lower()
                            # Filter out very short names if any (unlikely for full names)
                            if len(name_clean) >= 3:
                                target_keywords.add(name_clean)
                        
                        # Add Aliases (Strict Filtering)
                        if stock_obj.get('aliases'):
                            for alias in stock_obj['aliases']:
                                alias_clean = alias.lower().strip()
                                # Rule: Must be >= 3 chars OR contain a digit (e.g. "3m", "20m")
                                if len(alias_clean) >= 3 or any(c.isdigit() for c in alias_clean):
                                    target_keywords.add(alias_clean)
                
                # Strict Filter: Must appear in HEADLINE using WORD BOUNDARIES
                if target_keywords:
                    # Create a massive regex OR pattern: \b(term1|term2|term3)\b
                    # Sort by length descending to match longest phrases first (though regex engine handles this, it's safer)
                    sorted_keywords = sorted(target_keywords, key=len, reverse=True)
                    escaped_keywords = [re.escape(k) for k in sorted_keywords]
                    pattern_str = r'\b(' + '|'.join(escaped_keywords) + r')\b'
                    
                    try:
                        regex = re.compile(pattern_str, re.IGNORECASE)
                        
                        final_news = []
                        for item in all_news:
                            headline = str(item.get("headline") or "")
                            if regex.search(headline):
                                final_news.append(item)
                        
                        all_news = final_news
                    except Exception as e:
                        print(f"Regex error: {e}")
                        # Fallback to empty if regex fails
                        all_news = []
                else:
                    all_news = []

        # Global Search
        if q:
            query = q.lower().strip()
            all_news = [
                item for item in all_news 
                if query in str(item.get("headline") or "").lower() or 
                   query in str(item.get("description") or "").lower() or
                   query in str(item.get("category") or "").lower()
            ]

        # Filter Type (Trending, Week, etc.)
        now = datetime.now()
        if filter_type == 'trending':
            all_news = [item for item in all_news if (item.get("views") or 0) > 15]
        elif filter_type == 'week':
            all_news = [item for item in all_news if item.get("timestamp") and (now - datetime.strptime(item["timestamp"], "%d %b %Y, %I:%M %p")).days <= 7]
        # ... more time filters can be added here ...

        # 2. Sorting - CRITICAL: Sort by timestamp descending
        def get_timestamp(x):
            ts = x.get("timestamp")
            if not ts: return datetime.min
            try:
                # Handle formatted strings from our JSON
                return datetime.strptime(ts, "%d %b %Y, %I:%M %p")
            except:
                try:
                    # Fallback for ISO strings if any still exist
                    return datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except:
                    return datetime.min

        all_news.sort(key=get_timestamp, reverse=True)

        # 3. Pagination
        total_count = len(all_news)
        offset = (page - 1) * limit
        paginated_items = all_news[offset : offset + limit]
        
        return {
            "items": paginated_items,
            "total": total_count,
            "page": page,
            "pages": (total_count + limit - 1) // limit if limit > 0 else 1
        }

    except Exception as e:
        print(f"Error fetching news: {e}")
        return {"items": [], "total": 0, "page": 1, "pages": 1}

class ViewRequest(BaseModel):
    link: str

@app.post("/news/view")
def increment_view(request: ViewRequest, db: Session = Depends(get_db)):
    try:
        item = db.query(NewsAnalytics).filter(NewsAnalytics.news_link == request.link).first()
        if not item:
            item = NewsAnalytics(news_link=request.link, views=1)
            db.add(item)
        else:
            item.views += 1
        db.commit()
        return {"views": item.views}
    except Exception as e:
        print(f"Error incrementing view: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market")
def read_market():
    return get_market_data()

@app.get("/stock/{symbol}")
def read_stock_details(symbol: str):
    data = get_stock_details(symbol)
    if not data:
        raise HTTPException(status_code=404, detail="Stock not found")
    return data

@app.get("/stock/{symbol}/history")
def read_stock_history(symbol: str, period: str = "1mo"):
    data = get_stock_history(symbol, period)
    return data

@app.get("/stock/{symbol}/financials")
def read_stock_financials(symbol: str):
    data = get_stock_financials(symbol)
    return data

@app.post("/chat")
def chat(request: ChatRequest):
    response = get_chat_response(request.query)
    return {"response": response}

from chatbot import summarize_news

@app.post("/news/summary")
def get_news_summary(request: ViewRequest):
    # summarize_news returns a dict: {"summary": text, "sentiment": sentiment}
    result = summarize_news(request.link)
    if isinstance(result, str):
         # fallback if someone reverted chatbot.py or it returned string on error
         return {"summary": result}
    return result

@app.post("/auth/signup")
def signup(user: UserSignup, db: Session = Depends(get_db)):
    email_lower = user.email.lower()
    db_user = db.query(User).filter(User.email == email_lower).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        name=user.name,
        email=email_lower,
        password_hash=hash_password(user.password),
        dob=user.dob
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user": {"name": new_user.name, "email": new_user.email}}

@app.post("/auth/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    email_lower = user.email.lower()
    db_user = db.query(User).filter(User.email == email_lower).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    is_valid = verify_password(user.password, db_user.password_hash)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    return {
        "message": "Login successful",
        "user": {
            "name": db_user.name,
            "email": db_user.email,
            "dob": db_user.dob
        }
    }

@app.get("/search-stocks")
def search_stocks(q: str):
    if not q:
        return []
    query = q.lower()
    results = [
        s for s in NSE_STOCKS 
        if query in s["name"].lower() or query in s["symbol"].lower()
    ]
    return results

@app.get("/watchlist/{email}")
def get_watchlist(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return [{"symbol": item.symbol, "name": item.name} for item in user.watchlist]

@app.post("/watchlist")
def add_to_watchlist(request: WatchlistRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already exists
    exists = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id, 
        WatchlistItem.symbol == request.symbol
    ).first()
    
    if exists:
        return {"message": "Already in watchlist"}
    
    new_item = WatchlistItem(
        user_id=user.id,
        symbol=request.symbol,
        name=request.name or request.symbol
    )
    db.add(new_item)
    db.commit()
    return {"message": "Added to watchlist"}

@app.delete("/watchlist/{email}/{symbol}")
def remove_from_watchlist(email: str, symbol: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    item = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id, 
        WatchlistItem.symbol == symbol
    ).first()
    
    if item:
        db.delete(item)
        db.commit()
        return {"message": "Removed from watchlist"}
    
    raise HTTPException(status_code=404, detail="Item not found in watchlist")

@app.post("/debug/trigger-notifications")
def trigger_notifications_manual():
    if notification_manager:
        # Run primarily for debugging, so we allow it to block slightly
        notification_manager.check_and_notify()
        return {"message": "Notification check triggered manually."}
    return {"message": "Notification manager not initialized."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
