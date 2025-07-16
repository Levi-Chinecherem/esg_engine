"""
This module provides search functionality for the Reports RAG Database in the ESG Engine.
It queries the temporary FAISS index for a single report, supporting concurrent searches for multiple criteria,
returning top-k matches with metadata and context (target sentence, before, after).

file path: esg_engine/rag/reports_rag/searcher.py
"""

import os
import pickle
import faiss
import concurrent.futures
from utils.vector_utils import search_index
from utils.text_processing import tokenize_and_embed
from utils.resource_monitor import check_resources
from config.settings import get_settings

def search_report(criteria, k=5):
    """
    Queries the temporary FAISS index for multiple criteria concurrently, returning top-k matches
    with metadata and context (target sentence, before, after).
    
    Args:
        criteria (list): List of query strings to search for.
        k (int): Number of results per criterion. Defaults to 5.
    
    Returns:
        list: List of dictionaries with criterion, matches (metadata, distance, context).
    """
    # Load settings
    settings = get_settings()
    index_path = os.path.join(settings["data_paths"]["reports"], "temp_index.faiss")
    metadata_path = os.path.join(settings["data_paths"]["reports"], "temp_metadata.pkl")
    
    # Check if index and metadata exist
    if not (os.path.exists(index_path) and os.path.exists(metadata_path)):
        return []
    
    # Check resource limits
    if not check_resources():
        return []
    
    # Load metadata
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)
    
    # Load FAISS index
    index = faiss.read_index(index_path)
    
    def get_context(metadata, idx):
        """Helper function to retrieve context (before, after) for a sentence."""
        if idx < 0 or idx >= len(metadata):
            return None, None
        target = metadata[idx]["sentence"]
        before = metadata[idx-1]["sentence"] if idx > 0 and metadata[idx-1]["page_number"] == metadata[idx]["page_number"] else None
        after = metadata[idx+1]["sentence"] if idx < len(metadata)-1 and metadata[idx+1]["page_number"] == metadata[idx]["page_number"] else None
        return before, after
    
    def search_single_criterion(criterion):
        """Helper function to search for a single criterion."""
        query_page = [{"page_number": 1, "text": criterion}]
        query_results = tokenize_and_embed(query_page)
        if not query_results:
            return {"criterion": criterion, "matches": []}
        
        query_embedding = query_results[0]["embedding"]
        results = search_index(index, query_embedding, metadata_path, k=k)
        
        # Add context to results
        for res in results:
            idx = [i for i, m in enumerate(metadata) if m["sentence_index"] == res["sentence_index"] and m["page_number"] == res["page_number"]]
            if idx:
                res["before"], res["after"] = get_context(metadata, idx[0])
        
        return {"criterion": criterion, "matches": results}
    
    # Execute concurrent searches
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_criterion = {executor.submit(search_single_criterion, criterion): criterion for criterion in criteria}
        for future in concurrent.futures.as_completed(future_to_criterion):
            results.append(future.result())
    
    return results