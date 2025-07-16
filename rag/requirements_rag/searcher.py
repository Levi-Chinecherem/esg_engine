"""
This module provides search functionality for the Requirements RAG Database in the ESG Engine.
It retrieves requirements by app name (e.g., UNCTAD_requirements.csv) or query text, with fallback
to description-based searches, returning results with category, criterion, and description.

file path: esg_engine/rag/requirements_rag/searcher.py
"""

import os
import pickle
import faiss
from utils.text_processing import tokenize_and_embed
from utils.vector_utils import search_index, add_to_index
from utils.resource_monitor import check_resources
from config.settings import get_settings
import logging

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "requirements_searcher.log")
logging.basicConfig(filename=log_file, level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def search_requirements(query, app_name=None, k=5):
    """
    Searches the FAISS index for requirements matching the query, optionally filtered by app name,
    with fallback to description-based search if no matches are found.
    
    Args:
        query (str): Text query to search for.
        app_name (str, optional): CSV filename to filter results (e.g., "UNCTAD_requirements.csv").
        k (int): Number of results to return. Defaults to 5.
    
    Returns:
        list: List of dictionaries with category, criterion, description, app_name, and distance.
    """
    # Load settings
    settings = get_settings()
    index_path = os.path.join(settings["data_paths"]["requirements"], "index.faiss")
    metadata_path = os.path.join(settings["data_paths"]["requirements"], "metadata.pkl")
    
    # Check if index and metadata exist
    if not (os.path.exists(index_path) and os.path.exists(metadata_path)):
        logging.warning(f"Index or metadata not found at {index_path}, {metadata_path}")
        return []
    
    # Check resource limits
    if not check_resources():
        logging.error("Resource usage exceeds 45% limit, aborting search")
        return []
    
    # Embed query
    query_page = [{"page_number": 1, "text": query}]
    query_results = tokenize_and_embed(query_page)
    if not query_results:
        logging.warning("Failed to embed query")
        return []
    query_embedding = query_results[0]["embedding"]
    
    # Load FAISS index
    index = faiss.read_index(index_path)
    
    # Search index
    results = search_index(index, query_embedding, metadata_path, k=k)
    
    # Filter by app_name if provided
    if app_name:
        results = [res for res in results if res["app_name"] == app_name]
    
    # Fallback to description-based search if no results and no app_name filter
    if not results and not app_name:
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
        # Prepare descriptions for embedding
        description_texts = [{"page_number": 1, "text": m["description"]} for m in metadata]
        description_results = tokenize_and_embed(description_texts)
        if description_results:
            description_embeddings = [res["embedding"] for res in description_results]
            # Temporarily add description embeddings to index
            add_to_index(index, description_embeddings, metadata, metadata_path, index_path, temporary=True)
            results = search_index(index, query_embedding, metadata_path, k=k)
    
    # Format results
    formatted_results = [{
        "category": res["category"],
        "criterion": res["criterion"],
        "description": res["description"],
        "app_name": res["app_name"],
        "distance": res["distance"]
    } for res in results]
    
    return formatted_results