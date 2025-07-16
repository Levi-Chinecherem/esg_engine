"""
This module provides search functionality for the Standards RAG Database in the ESG Engine.
It queries the FAISS index by text, supporting optional filtering by document name (e.g., ifrs_s1.pdf),
and returns top-k matches with metadata.

file path: esg_engine/rag/standards_rag/searcher.py
"""

import os
import faiss
from utils.vector_utils import search_index
from utils.text_processing import tokenize_and_embed
from config.settings import get_settings

def search_standards(query, document_filter=None, k=5):
    """
    Queries the FAISS index for the top-k closest sentences to the input query, optionally
    filtered by document name.
    
    Args:
        query (str): Text query to search for.
        document_filter (str, optional): Document name to filter results (e.g., "ifrs_s1.pdf").
        k (int): Number of results to return. Defaults to 5.
    
    Returns:
        list: List of dictionaries with metadata (document_name, page_number, sentence_index, sentence, distance).
    """
    # Load settings
    settings = get_settings()
    index_path = os.path.join(settings["data_paths"]["standards"], "index.faiss")
    metadata_path = os.path.join(settings["data_paths"]["standards"], "metadata.pkl")
    
    # Check if index and metadata exist
    if not (os.path.exists(index_path) and os.path.exists(metadata_path)):
        return []
    
    # Embed query
    query_page = [{"page_number": 1, "text": query}]
    query_results = tokenize_and_embed(query_page)
    if not query_results:
        return []
    query_embedding = query_results[0]["embedding"]
    
    # Load FAISS index
    index = faiss.read_index(index_path)
    
    # Search index
    results = search_index(index, query_embedding, metadata_path, k=k)
    
    # Apply document filter if provided
    if document_filter:
        results = [res for res in results if res["document_name"] == document_filter]
    
    return results