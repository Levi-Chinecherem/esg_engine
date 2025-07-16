"""
This file contains unit tests for the Standards RAG Database, testing indexing, searching,
and updating with real standards (ifrs_s1.pdf, ifrs_s2.pdf, ESRS_2.pdf).

file path: esg_engine/tests/test_standards_rag.py
"""

import pytest
import os
import time
from rag.standards_rag.indexer import index_standards
from rag.standards_rag.searcher import search_standards
from rag.standards_rag.updater import update_standards
from config.settings import get_settings
from utils.resource_monitor import check_resources

def test_index_standards():
    """
    Tests indexing of real standards PDFs (ifrs_s1.pdf, ifrs_s2.pdf, ESRS_2.pdf).
    """
    settings = get_settings()
    standards_dir = settings["data_paths"]["standards"]
    index_path = os.path.join(standards_dir, "index.faiss")
    metadata_path = os.path.join(standards_dir, "metadata.pkl")
    
    # Check if standards exist
    standards = ["ifrs_s1.pdf", "ifrs_s2.pdf", "ESRS_2.pdf"]
    if not all(os.path.exists(os.path.join(standards_dir, f)) for f in standards):
        pytest.skip("Not all standards PDFs found in data/standards/")
    
    # Index standards and measure time
    start_time = time.time()
    index_standards()
    assert time.time() - start_time < 60, "Indexing took longer than 1 minute"
    
    # Verify index and metadata
    assert os.path.exists(index_path), "Index file not created"
    assert os.path.exists(metadata_path), "Metadata file not created"
    
    # Check metadata content
    import pickle
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)
    assert len(metadata) > 0, "No metadata generated"
    assert any(m["document_name"] == "ifrs_s1.pdf" for m in metadata)
    assert any(m["document_name"] == "ifrs_s2.pdf" for m in metadata)
    assert any(m["document_name"] == "ESRS_2.pdf" for m in metadata)
    
    # Check resource usage
    assert check_resources(), "Resource usage exceeded 45% limit"

def test_search_standards():
    """
    Tests searching the FAISS index with and without document filtering.
    """
    settings = get_settings()
    standards_dir = settings["data_paths"]["standards"]
    
    # Ensure index exists
    index_standards()  # Rebuild index to ensure it’s fresh
    
    # Test search with a sample ESG query
    query = "sustainability reporting requirements"
    start_time = time.time()
    results = search_standards(query, document_filter="ifrs_s1.pdf", k=5)
    assert time.time() - start_time < 0.5, "Search took longer than 0.5 seconds"
    assert isinstance(results, list), "Results should be a list"
    assert all(res["document_name"] == "ifrs_s1.pdf" for res in results), "Filter not applied"
    
    # Test full search (no filter)
    results = search_standards(query, k=5)
    assert any(res["document_name"] in ["ifrs_s1.pdf", "ifrs_s2.pdf", "ESRS_2.pdf"] for res in results)
    
    # Test empty query
    results = search_standards("")
    assert results == [], "Empty query should return empty results"
    
    # Test missing index
    os.remove(os.path.join(standards_dir, "index.faiss"))
    results = search_standards(query)
    assert results == [], "Missing index should return empty results"

def test_update_standards():
    """
    Tests updating the FAISS index when a new standard is added.
    """
    settings = get_settings()
    standards_dir = settings["data_paths"]["standards"]
    
    # Start updater in a separate thread
    import threading
    update_thread = threading.Thread(target=update_standards, daemon=True)
    update_thread.start()
    
    # Simulate adding a new PDF
    new_pdf = os.path.join(standards_dir, "new_standard.pdf")
    with open(new_pdf, "w") as f:
        f.write("Test standard text.")  # Simulate a new PDF
    
    # Wait for update
    time.sleep(2)
    
    # Verify index and metadata
    metadata_path = os.path.join(standards_dir, "metadata.pkl")
    assert os.path.exists(metadata_path), "Metadata file not created"
    with open(metadata_path, "rb") as f:
        import pickle
        metadata = pickle.load(f)
    assert any(m["document_name"] == "new_standard.pdf" for m in metadata), "New standard not indexed"
    
    # Cleanup
    os.remove(new_pdf)