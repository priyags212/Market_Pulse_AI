import yfinance as yf
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import datetime

# --- Configuration ---
VECTOR_DB_PATH = "./chroma_db"
COLLECTION_NAME = "financial_reports"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# --- Initialize Vector DB ---
try:
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    
    # Use SentenceTransformer embeddings
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )
    
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=sentence_transformer_ef
    )
    print(f"Vector DB initialized at {VECTOR_DB_PATH}")
except Exception as e:
    print(f"Error initializing ChromaDB: {e}")
    collection = None

# --- Ingestion Logic ---

def fetch_quarterly_data(ticker_symbol):
    """
    Fetches latest quarterly financials for a ticker.
    Returns textual chunks describing the results.
    """
    try:
        # Resolve symbol
        search_symbol = ticker_symbol.strip()
             
        ticker = yf.Ticker(search_symbol)
        chunks = []

        # 1. Income Statement
        inc = ticker.quarterly_income_stmt
        if not inc.empty:
            # Get latest 2 quarters
            latest_dates = inc.columns[:2]
            
            for date in latest_dates:
                date_str = date.strftime('%Y-%m-%d')
                col = inc[date]
                
                revenue = col.get("Total Revenue", "N/A")
                net_income = col.get("Net Income", "N/A")
                ebitda = col.get("EBITDA", "N/A")
                basic_eps = col.get("Basic EPS", "N/A")
                
                # Create a descriptive text chunk
                chunk_text = (
                    f"Financial Results for {search_symbol} (Quarter ending {date_str}):\n"
                    f"- Total Revenue: {revenue}\n"
                    f"- Net Income: {net_income}\n"
                    f"- EBITDA: {ebitda}\n"
                    f"- Basic EPS: {basic_eps}\n"
                )
                
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "ticker": ticker_symbol,
                        "date": date_str,
                        "type": "income_statement"
                    },
                    "id": f"{ticker_symbol}_{date_str}_income"
                })

        # 2. Recent Price History (Last 5 Days)
        try:
            hist = ticker.history(period="5d")
            if not hist.empty:
                # Iterate over the last 5 days (or fewer if less data)
                # hist index is the Date
                for date, row in hist.iterrows():
                    date_str = date.strftime('%Y-%m-%d')
                    close_price = round(row['Close'], 2)
                    volume = int(row['Volume'])
                    open_price = round(row['Open'], 2)
                    high_price = round(row['High'], 2)
                    low_price = round(row['Low'], 2)

                    # Create a descriptive text chunk for Price
                    price_chunk_text = (
                        f"Stock Price for {search_symbol} on {date_str}:\n"
                        f"- Closing Price: {close_price}\n"
                        f"- Volume: {volume}\n"
                        f"- Open: {open_price}\n"
                        f"- High: {high_price}\n"
                        f"- Low: {low_price}\n"
                    )
                    
                    chunks.append({
                        "text": price_chunk_text,
                        "metadata": {
                            "ticker": ticker_symbol,
                            "date": date_str,
                            "type": "stock_price"
                        },
                        "id": f"{ticker_symbol}_{date_str}_price"
                    })
        except Exception as e:
            print(f"Error fetching price history for {ticker_symbol}: {e}")
            
        return chunks

    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")
        return []

def ingest_financial_data(tickers):
    """
    Orchestrates fetching and storing data for multiple tickers.
    """
    if not collection:
        print("Vector DB not initialized.")
        return

    print(f"Starting ingestion for: {tickers}")
    total_chunks = 0
    
    for ticker in tickers:
        chunks = fetch_quarterly_data(ticker)
        if not chunks:
            continue
            
        ids = [c["id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        # Upsert into ChromaDB
        # First, delete existing data for this ticker to prevent duplicates/staleness
        try:
            print(f"Clearing old data for {ticker}...")
            collection.delete(where={"ticker": ticker})
        except Exception as e:
            print(f"Warning: Could not delete old data for {ticker}: {e}")

        collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        total_chunks += len(chunks)
        print(f"Ingested {len(chunks)} chunks for {ticker}")
        
    print(f"Ingestion complete. Total chunks: {total_chunks}")

# --- Dynamic Ingestion Logic ---

def extract_ticker_from_query(query: str) -> str:
    """
    Uses Llama 3.2 to extract the likely NSE stock symbol from a query.
    e.g., "Tell me about Dabur" -> "DABUR.NS"
    """
    import requests
    import json
    import re

    # 1. High-Confidence Regex/Keyword Match (Prioritized over LLM)
    query_upper = query.upper()
    common_mappings = {
        "TCS": "TCS.NS",
        "RELIANCE": "RELIANCE.NS",
        "INFY": "INFY.NS",
        "HDFC": "HDFCBANK.NS",
        "TATA MOTORS": "TATAMOTORS.NS",
        "TATA STEEL": "TATASTEEL.NS",
        "INFOSYS": "INFY.NS",
        "MORNINGSTAR": "MORN"
    }
    
    for key, value in common_mappings.items():
        if key in query_upper:
            print(f"Keyword Extraction: Found {key} -> {value}")
            return value

    # 2. LLM Extraction (Fallback for complex/unknown queries)
    system_prompt = (
        "You are an expert financial ticker extractor. Your goal is to identify the company in the user's query and return its stock ticker.\n"
        "Rules:\n"
        "1. Identify the company name (e.g., 'TCS', 'Reliance', 'Apple').\n"
        "2. If it is an Indian company, append '.NS' (e.g., 'RELIANCE.NS', 'TCS.NS').\n"
        "3. If it is a US company, return the standard ticker (e.g., 'AAPL', 'TSLA').\n"
        "4. If uncertain or no company is mentioned, return 'NONE'.\n"
        "Examples:\n"
        "- 'TCS closing price' -> 'TCS.NS'\n"
        "- 'Morningstar results' -> 'MORN'\n"
        "- 'Apple news' -> 'AAPL'\n"
        "- 'Reliance revenue' -> 'RELIANCE.NS'\n"
        "- 'Tata Motors' -> 'TATAMOTORS.NS'\n"
        "Return ONLY the symbol string."
    )
    
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                "stream": False,
                "options": {"temperature": 0.1} # Deterministic
            },
            timeout=10
        )
        if response.status_code == 200:
            symbol = response.json().get("message", {}).get("content", "").strip()
            # Relaxed validation: Allow symbols without dots (US stocks)
            if symbol and symbol != "NONE": 
                # Cleanup: remove any trailing periods or whitespace
                return symbol.strip(".")
    except Exception as e:
        print(f"Error extracting ticker: {e}")
        

    


    return None

def ensure_ticker_ingested(ticker: str):
    """
    Checks if a ticker is present in the DB and if the data is fresh. 
    If not found or stale (older than ~1 day), ingests it.
    """
    if not collection:
        return

    # 1. Check for recent price data
    # We look for a 'stock_price' chunk with a recent date
    try:
        # Get today's date
        today = datetime.datetime.now().date()
        recent_cutoff = today - datetime.timedelta(days=2) # Allow max 2 days staleness (weekends)

        # Query specifically for this ticker's price data
        results = collection.get(
            where={
                "$and": [
                    {"ticker": {"$eq": ticker}},
                    {"type": {"$eq": "stock_price"}}
                ]
            },
            include=["metadatas"] # We only need metadata to check dates
        )
        
        is_fresh = False
        if results and results['metadatas']:
            # Check if any chunk has a date >= recent_cutoff
            for meta in results['metadatas']:
                 if not meta: continue # Safeguard against None
                 
                 chunk_date_str = meta.get("date")
                 if chunk_date_str:
                     try:
                         # Dates are typically YYYY-MM-DD
                         chunk_date = datetime.datetime.strptime(chunk_date_str, "%Y-%m-%d").date()
                         if chunk_date >= recent_cutoff:
                             is_fresh = True
                             break
                     except ValueError:
                         continue
        
        if is_fresh:
            # print(f"Data for {ticker} is fresh.")
            return

        print(f"Data for {ticker} is missing or stale. Fetching live data...")
        ingest_financial_data([ticker])

    except Exception as e:
        print(f"Error checking freshness for {ticker}: {e}")
        # Fallback: try ingest just in case
        ingest_financial_data([ticker])

def ingest_news_articles(news_items):
    """
    Ingests news articles into the vector database.
    Each article is stored as a document with metadata.
    """
    if not collection:
        print("Vector DB not initialized.")
        return

    # Filter valid items
    valid_items = [item for item in news_items if item.get("full_content") or item.get("headline")]
    
    if not valid_items:
        return

    print(f"Ingesting {len(valid_items)} news articles into Vector DB...")
    
    ids = []
    documents = []
    metadatas = []
    
    for item in valid_items:
        # Create a unique ID from the link
        doc_id = item.get("link", "")
        if not doc_id:
            continue
            
        headline = item.get("headline", "No Title")
        timestamp = item.get("timestamp", "Unknown Date")
        content = item.get("full_content", "")
        
        # If content is empty/short, use description or headline
        if not content:
            content = item.get("description", headline)
            
        # Construct the text to embed
        # We limit content to approx first 2000 chars to stay within reasonable embedding limits 
        # (though model truncates, this saves network/processing if we were remote)
        # Detailed format helping the LLM understand this is a News Article
        doc_text = (
            f"News Article: {headline}\n"
            f"Date: {timestamp}\n"
            f"Content: {content[:4000]}" 
        )
        
        ids.append(doc_id)
        documents.append(doc_text)
        metadatas.append({
            "type": "news",
            "headline": headline,
            "date": timestamp,
            "link": doc_id
        })
        
    if ids:
        try:
            # Batch upsert
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"Successfully ingested {len(ids)} news articles.")
        except Exception as e:
            print(f"Error ingesting news: {e}")


# --- Retrieval Logic ---

def retrieve_context(query, k=3):
    """
    Semantic search for relevant financial context.
    Now supports Dynamic RAG:
    1. Extract Ticker
    2. Ensure Data Exists
    3. Query
    """
    if not collection:
        return ""
    
    # 1. Dynamic Step
    extracted_ticker = extract_ticker_from_query(query)
    search_filter = None
    
    if extracted_ticker:
        print(f"Identified Stock: {extracted_ticker}")
        ensure_ticker_ingested(extracted_ticker)
        search_filter = {"ticker": extracted_ticker}
        
    results = collection.query(
        query_texts=[query],
        n_results=5, # Increased k to capture price + financials
        where=search_filter # Apply filter if ticker known
    )
    
    # Flatten results
    documents = results['documents'][0]
    
    if not documents:
        return ""
        
    # Format as a single string
    context_str = "\n".join(documents)
    return context_str

if __name__ == "__main__":
    # Test Ingestion
    test_tickers = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
    ingest_financial_data(test_tickers)
    
    # Test Retrieval
    q = "Compare Reliance and TCS revenue"
    print(f"\nQuery: {q}")
    ctx = retrieve_context(q)
    print(f"Retrieved Context:\n{ctx}")
