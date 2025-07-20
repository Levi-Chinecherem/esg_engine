"""
This module searches the FAISS index for requirements matching a query in the ESG Engine.

file path: esg_engine/rag/requirements_rag/searcher.py
"""

import os
import logging
import faiss
import pickle
import numpy as np
import csv
from config.settings import get_settings
from utils.text_processing import tokenize_and_embed

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "requirements.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def search_requirements(query, app_name=None, k=1000):
    """
    Searches the FAISS index for requirements matching the query, optionally filtered by app_name.
    If query is empty, returns all requirements for the specified app_name from cached texts.

    Args:
        query (str): Text query to search for (can be empty).
        app_name (str, optional): CSV filename to filter results (e.g., "UNCTAD_requirements.csv").
        k (int): Maximum number of results to return. Defaults to 1000.

    Returns:
        list: List of dictionaries with criterion, description, document_name, category, and distance (if queried).
    """
    try:
        logging.info(f"Searching requirements for query='{query}', app_name='{app_name}', k={k}")

        # Load settings
        standards_dir = settings["data_paths"]["standards"]
        requirements_dir = settings["data_paths"].get("requirements", standards_dir)
        index_path = os.path.join(standards_dir, "index.faiss")
        metadata_path = os.path.join(standards_dir, "metadata.pkl")
        text_cache_path = os.path.join(standards_dir, "texts_cache.pkl")

        # Check for cached texts
        if not os.path.exists(text_cache_path):
            logging.error(f"No text cache found at {text_cache_path}. Run indexer.py first.")
            return []

        with open(text_cache_path, "rb") as f:
            cached_texts = pickle.load(f)
        logging.info(f"Loaded cached texts: {len(cached_texts['standards'])} standards, {len(cached_texts['requirements'])} requirements")

        # Load metadata
        if not os.path.exists(metadata_path):
            logging.error(f"Metadata not found at {metadata_path}. Run indexer.py first.")
            return []
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
        logging.info(f"Loaded metadata with {len(metadata)} entries")

        # Load category mapping from CSV if available
        category_mapping = {}
        if app_name and os.path.exists(os.path.join(requirements_dir, app_name)):
            with open(os.path.join(requirements_dir, app_name), "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    criterion = row["criterion"]
                    category = row.get("category", "Unknown")
                    category_mapping[criterion] = category
            logging.info(f"Loaded category mapping for {len(category_mapping)} criteria from {app_name}")

        # Handle empty query
        if not query.strip():
            logging.info(f"Empty query provided, returning all requirements for app_name='{app_name}'")
            if app_name and app_name in cached_texts["requirements"]:
                req_texts = cached_texts["requirements"][app_name]
                requirements = [
                    {
                        "criterion": text.split(":", 1)[0],
                        "description": text.split(":", 1)[1] if ":" in text else "",
                        "document_name": app_name,
                        "category": category_mapping.get(text.split(":", 1)[0], "Unknown")
                    }
                    for text in req_texts.values()
                ]
                logging.info(f"Returning {len(requirements)} cached requirements for {app_name}")
                return requirements[:k]
            logging.warning(f"No requirements found for app_name='{app_name}' in cache")
            return []

        # Check if index exists
        if not os.path.exists(index_path):
            logging.error(f"Index not found at {index_path}. Run indexer.py first.")
            return []

        # Embed query
        query_page = [{"page_number": 1, "text": query}]
        query_results = tokenize_and_embed(query_page)
        if not query_results:
            logging.warning(f"Failed to embed query '{query}'")
            if app_name and app_name in cached_texts["requirements"]:
                req_texts = cached_texts["requirements"][app_name]
                requirements = [
                    {
                        "criterion": text.split(":", 1)[0],
                        "description": text.split(":", 1)[1] if ":" in text else "",
                        "document_name": app_name,
                        "category": category_mapping.get(text.split(":", 1)[0], "Unknown")
                    }
                    for text in req_texts.values()
                ]
                return requirements[:k]
            return []

        query_embedding = query_results[0]["embedding"]
        logging.info(f"Query embedded successfully: {query_embedding.shape}")

        # Load FAISS index
        try:
            index = faiss.read_index(index_path)
            logging.info(f"Loaded FAISS index with {index.ntotal} vectors")
        except Exception as e:
            logging.error(f"Failed to load FAISS index: {str(e)}")
            if app_name and app_name in cached_texts["requirements"]:
                req_texts = cached_texts["requirements"][app_name]
                requirements = [
                    {
                        "criterion": text.split(":", 1)[0],
                        "description": text.split(":", 1)[1] if ":" in text else "",
                        "document_name": app_name,
                        "category": category_mapping.get(text.split(":", 1)[0], "Unknown")
                    }
                    for text in req_texts.values()
                ]
                return requirements[:k]
            return []

        # Search index
        try:
            distances, indices = index.search(np.array([query_embedding], dtype=np.float32), k)
            logging.info(f"FAISS search returned {len(indices[0])} indices")
        except Exception as e:
            logging.error(f"FAISS search failed: {str(e)}")
            if app_name and app_name in cached_texts["requirements"]:
                req_texts = cached_texts["requirements"][app_name]
                requirements = [
                    {
                        "criterion": text.split(":", 1)[0],
                        "description": text.split(":", 1)[1] if ":" in text else "",
                        "document_name": app_name,
                        "category": category_mapping.get(text.split(":", 1)[0], "Unknown")
                    }
                    for text in req_texts.values()
                ]
                return requirements[:k]
            return []

        # Collect results
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(metadata):
                result = metadata[idx].copy()
                if result.get("type") == "requirement" and (not app_name or result.get("document_name") == app_name):
                    criterion = result["sentence"].split(":", 1)[0]
                    results.append({
                        "criterion": criterion,
                        "description": result["sentence"].split(":", 1)[1] if ":" in result["sentence"] else "",
                        "document_name": result["document_name"],
                        "category": category_mapping.get(criterion, "Unknown"),
                        "distance": float(dist)
                    })
        logging.info(f"Filtered {len(results)} requirements matching app_name='{app_name}'")

        return results[:k]

    except Exception as e:
        logging.error(f"Search requirements failed: {str(e)}", exc_info=True)
        return []