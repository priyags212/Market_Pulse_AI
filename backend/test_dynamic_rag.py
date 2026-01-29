from rag_engine import retrieve_context

print("--- Testing Dynamic RAG for New Stock ---")
query = "Tell me about Dabur Q3 results"
print(f"Query: {query}")

# This should trigger auto-ingestion for DABUR.NS
context = retrieve_context(query)

print("\n--- Retrieved Context ---")
print(context if context else "No context retrieved.")
