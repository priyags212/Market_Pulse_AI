import sys
import os
import chromadb

# Add the current directory to sys.path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def inspect_tcs_db():
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("financial_reports")
    
    print("--- Inspecting TCS Chunks ---")
    
    # Query all chunks where text contains "TCS"
    # Note: Chroma get() where filter is exact match for metadata usually, or we can just fetch all and filter in python for debug
    
    results = collection.get(
        where_document={"$contains": "TCS"},
        include=["metadatas", "documents"]
    )
    
    if not results['ids']:
        print("No chunks found with metadata ticker='TCS.NS'")
        # Try finding without specific ticker metadata just in case
        results = collection.get(
             where_document={"$contains": "TCS"},
             include=["metadatas", "documents"]
        )
        print(f"Found {len(results['ids'])} chunks containing 'TCS' in text.")
    else:
        print(f"Found {len(results['ids'])} chunks with metadata ticker='TCS.NS'")

    for i, doc_id in enumerate(results['ids']):
        meta = results['metadatas'][i]
        doc = results['documents'][i]
        print(f"\n[ID: {doc_id}]")
        print(f"Metadata: {meta}")
        print(f"Content (first 200 chars): {doc[:200]}...")

if __name__ == "__main__":
    inspect_tcs_db()
