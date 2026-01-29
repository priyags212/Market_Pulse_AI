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
        # Resolve symbol (NSE default)
        search_symbol = ticker_symbol
        if not ticker_symbol.endswith(".NS") and not ticker_symbol.endswith(".BO"):
             search_symbol = f"{ticker_symbol}.NS"
             
        ticker = yf.Ticker(search_symbol)
        
        # 1. Income Statement
        inc = ticker.quarterly_income_stmt
        if inc.empty:
            print(f"No income statement found for {search_symbol}")
            return []
            
        # Get latest 2 quarters
        latest_dates = inc.columns[:2]
        
        chunks = []
        
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
    
    system_prompt = (
        "You are a financial entity extractor. Your ONLY job is to extract the likely NSE stock symbol from the user's query. "
        "Append '.NS' to the symbol. If no specific company is mentioned, return 'NONE'. "
        "Examples:\n"
        "- 'How is Reliance performing?' -> 'RELIANCE.NS'\n"
        "- 'Tell me about Tata Motors results' -> 'TATAMOTORS.NS'\n"
        "- 'What is the market looking like?' -> 'NONE'\n"
        "- 'Dabur Q3 results' -> 'DABUR.NS'\n"
        "Return ONLY the symbol string, no whitespace or punctuation."
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
                "options": {"temperature": 0} # Deterministic
            },
            timeout=5
        )
        if response.status_code == 200:
            symbol = response.json().get("message", {}).get("content", "").strip()
            if symbol and symbol != "NONE" and "." in symbol: # Basic validation
                return symbol
    except Exception as e:
        print(f"Error extracting ticker: {e}")
        
    return None

def ensure_ticker_ingested(ticker: str):
    """
    Checks if a ticker is present in the DB. If not, ingests it.
    """
    if not collection:
        return

    # Check existence - simple query on metadata
    # ChromaDB logic: if we can't find any documents for this ticker, ingest.
    # Note: query() is semantic, get() is direct. Use get() for existence check.
    existing = collection.get(
        where={"ticker": ticker},
        limit=1
    )
    
    if existing and existing['ids']:
        # Data exists, maybe implement TTL later, but for now skip
        return
        
    print(f"Ticker {ticker} not found in knowledge base. Auto-ingesting...")
    ingest_financial_data([ticker])


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
    if extracted_ticker:
        print(f"Identified Stock: {extracted_ticker}")
        ensure_ticker_ingested(extracted_ticker)
        
    results = collection.query(
        query_texts=[query],
        n_results=k
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
