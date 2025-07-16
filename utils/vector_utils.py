"""
This module provides functionality to manage FAISS indexes for the ESG Engine, including
initialization, adding embeddings, and searching. Indexes are stored on disk to minimize RAM usage.

file path: esg_engine/utils/vector_utils.py
"""

import faiss
import numpy as np
import pickle
import os

def initialize_index(dimension, index_path):
    """
    Initializes a FAISS FlatL2 index stored on disk.
    
    Args:
        dimension (int): Embedding dimension (e.g., 384 for all-MiniLM-L6-v2).
        index_path (str): Path to store the index file.
    
    Returns:
        faiss.Index: Initialized FAISS index.
    """
    # Create a FlatL2 index
    index = faiss.IndexFlatL2(dimension)
    # Enable disk storage
    faiss.write_index(index, index_path)
    return index

def add_to_index(index, embeddings, metadata, metadata_path, index_path):
    """
    Adds embeddings and metadata to a FAISS index and saves it to disk.
    
    Args:
        index (faiss.Index): FAISS index to add to.
        embeddings (np.ndarray): Array of embeddings.
        metadata (list): List of metadata dictionaries.
        metadata_path (str): Path to store metadata.
        index_path (str): Path to store the updated FAISS index.
    
    Returns:
        None
    """
    # Ensure embeddings are in correct format
    embeddings = np.array(embeddings, dtype=np.float32)
    
    # Add embeddings to index
    index.add(embeddings)
    
    # Save updated index to disk
    faiss.write_index(index, index_path)
    
    # Save metadata to disk
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f)

def search_index(index, query_embedding, metadata_path, k=5):
    """
    Searches the FAISS index for the top-k closest embeddings.
    
    Args:
        index (faiss.Index): FAISS index to search.
        query_embedding (np.ndarray): Query embedding.
        metadata_path (str): Path to metadata file.
        k (int): Number of results to return.
    
    Returns:
        list: List of dictionaries with metadata and distances.
    """
    # Load metadata
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)
    
    # Search index
    query_embedding = np.array([query_embedding], dtype=np.float32)
    distances, indices = index.search(query_embedding, k)
    
    # Collect results
    results = []
    for idx, distance in zip(indices[0], distances[0]):
        if idx < len(metadata):  # Ensure valid index
            result = metadata[idx].copy()
            result["distance"] = float(distance)
            results.append(result)
    
    return results