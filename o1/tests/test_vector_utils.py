"""
This file contains unit tests for the vector_utils module, testing FAISS index operations
with embeddings from btg-pactual.pdf.

file path: esg_engine/tests/test_vector_utils.py
"""

import pytest
import numpy as np
import os
from utils.vector_utils import initialize_index, add_to_index, search_index
from utils.pdf_processing import extract_pdf_text
from utils.text_processing import tokenize_and_embed
from config.settings import get_settings

def test_vector_operations_btg_pactual(tmp_path):
    """
    Tests FAISS index operations with embeddings from btg-pactual.pdf.
    """
    settings = get_settings()
    pdf_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    index_path = str(tmp_path / "test_index.faiss")
    metadata_path = str(tmp_path / "test_metadata.pkl")
    dimension = 384
    
    if not os.path.exists(pdf_path):
        pytest.skip("btg-pactual.pdf not found in data/reports/")
    
    # Extract and process text from btg-pactual.pdf
    pages = extract_pdf_text(pdf_path)
    assert len(pages) > 0, "No text extracted from PDF"
    
    results = tokenize_and_embed(pages)
    assert len(results) > 0, "No embeddings generated"
    
    # Initialize index
    index = initialize_index(dimension, index_path)
    assert os.path.exists(index_path), "Index file not created"
    
    # Add embeddings and metadata
    embeddings = np.array([res["embedding"] for res in results])
    metadata = [{"sentence": res["sentence"], "page_number": res["page_number"]} for res in results]
    add_to_index(index, embeddings, metadata, metadata_path, index_path)
    assert os.path.exists(metadata_path), "Metadata file not created"
    assert os.path.exists(index_path), "Index file not updated"
    
    # Search index
    query_embedding = results[0]["embedding"]
    search_results = search_index(index, query_embedding, metadata_path, k=2)
    assert len(search_results) <= 2, "Unexpected number of search results"
    assert all("sentence" in res and "page_number" in res and "distance" in res for res in search_results)