
import os
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from rag_engine import retrieve_context
from chatbot import get_chat_response

# --- Configuration ---
# Use the same model for generation and evaluation to keep it local
EVAL_MODEL = "llama3.2" 

# --- Prepare Dataset ---
# Ground truth data based on the "ingest_financial_data" we just ran/know about
# For real world, this should be manually curated.
data_samples = {
    'question': [
        'What was the total revenue of Reliance Industries in the quarter ending Dec 2024?',
        'Compare the Net Income of TCS and Reliance for Dec 2024.',
        'What is the Basic EPS of Infosys for the latest available quarter?'
    ],
    'ground_truth': [
        'Reliance Industries reported a Total Revenue of 2.64 Trillion INR (2,649,050,000,000) for the quarter ending 2025-12-31.', # adjusted based on what yfinance usually returns/what we saw
        'Reliance Net Income was 186.45 Billion INR. TCS Net Income data for Dec 2024 needs to be checked from context.', 
        'Infosys Basic EPS needs to be checked from context.'
    ]
}

def generate_rag_outputs():
    """
    Runs the RAG pipeline for the questions to generate 'answer' and 'contexts'.
    """
    questions = data_samples['question']
    answers = []
    contexts = []

    print("Generating responses for evaluation...")
    for q in questions:
        # 1. Retrieve Context
        # Note: chatbot.get_chat_response already calls retrieve_context internally now,
        # but for RAGAS we need the raw context list explicitly.
        # So we call retrieve_context separately to capture it for the metric.
        raw_context_str = retrieve_context(q)
        # RAGAS expects a list of strings for context
        ctx_list = [raw_context_str] if raw_context_str else []
        
        # 2. Generate Answer
        # We call the chatbot which *also* retrieves, but that's fine.
        ans = get_chat_response(q)
        
        answers.append(ans)
        contexts.append(ctx_list)
        print(f"Q: {q}\nA: {ans[:50]}...\n")
        
    return {
        'question': questions,
        'answer': answers,
        'contexts': contexts,
        'ground_truth': data_samples['ground_truth']
    }

def run_evaluation():
    # 1. Prepare Data
    data_dict = generate_rag_outputs()
    
    print("\n=== RAG Pipeline Verification ===")
    for i, q in enumerate(data_dict['question']):
        print(f"\nQuestion: {q}")
        print(f"Answer: {data_dict['answer'][i]}")
        print(f"Retrieved Context Snippet: {data_dict['contexts'][i][0][:200]}..." if data_dict['contexts'][i] else "No Context")
        print("-" * 50)

if __name__ == "__main__":
    run_evaluation()
