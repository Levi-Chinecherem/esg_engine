"""
This file contains unit tests for the Reports RAG Database, testing indexing, searching,
and cleanup with a real ESG report (btg-pactual.pdf).

file path: esg_engine/tests/test_reports_rag.py
"""

import pytest
import os
import time
from rag.reports_rag.indexer import index_report
from rag.reports_rag.searcher import search_report
from rag.reports_rag.cleaner import clean_report_index
from config.settings import get_settings
from utils.resource_monitor import check_resources

def test_index_report():
    """
    Tests indexing of btg-pactual.pdf.
    """
    settings = get_settings()
    report_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    index_path = os.path.join(settings["data_paths"]["reports"], "temp_index.faiss")
    metadata_path = os.path.join(settings["data_paths"]["reports"], "temp_metadata.pkl")
    
    # Check if report exists
    if not os.path.exists(report_path):
        pytest.skip("btg-pactual.pdf not found in data/reports/")
    
    # Index report and measure time
    start_time = time.time()
    assert index_report(report_path), "Indexing failed"
    assert time.time() - start_time < 60, "Indexing took longer than 1 minute"
    
    # Verify index and metadata
    assert os.path.exists(index_path), "Index file not created"
    assert os.path.exists(metadata_path), "Metadata file not created"
    
    # Check metadata content
    import pickle
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)
    assert len(metadata) > 0, "No metadata generated"
    assert all(m["document_name"] == "btg-pactual.pdf" for m in metadata)
    
    # Check resource usage
    assert check_resources(), "Resource usage exceeded 45% limit"

def test_search_report():
    """
    Tests concurrent searching of the FAISS index with multiple criteria.
    """
    settings = get_settings()
    report_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    
    # Index report
    if not os.path.exists(report_path):
        pytest.skip("btg-pactual.pdf not found in data/reports/")
    assert index_report(report_path), "Indexing failed"
    
    # Test concurrent searches
    criteria = ["sustainability", "emissions", "governance", "social impact", "compliance"]
    start_time = time.time()
    results = search_report(criteria, k=2)
    assert time.time() - start_time < 1, "Search took longer than 1 second"
    
    # Verify results
    assert len(results) == len(criteria), "Incorrect number of results"
    for res in results:
        assert "criterion" in res and "matches" in res
        assert isinstance(res["matches"], list)
        for match in res["matches"]:
            assert all(key in match for key in ["document_name", "page_number", "sentence_index", "sentence", "distance"])
            assert match["document_name"] == "btg-pactual.pdf"
            assert isinstance(match["before"], (str, type(None)))
            assert isinstance(match["after"], (str, type(None)))
    
    # Test empty criteria
    results = search_report([])
    assert results == [], "Empty criteria should return empty results"
    
    # Test missing index
    clean_report_index()
    results = search_report(criteria)
    assert results == [], "Missing index should return empty results"

def test_clean_report_index():
    """
    Tests cleanup of temporary FAISS index and metadata.
    """
    settings = get_settings()
    report_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    index_path = os.path.join(settings["data_paths"]["reports"], "temp_index.faiss")
    metadata_path = os.path.join(settings["data_paths"]["reports"], "temp_metadata.pkl")
    
    # Index report to create files
    if not os.path.exists(report_path):
        pytest.skip("btg-pactual.pdf not found in data/reports/")
    assert index_report(report_path), "Indexing failed"
    
    # Clean up and verify
    assert clean_report_index(), "Cleanup failed"
    assert not os.path.exists(index_path), "Index file not deleted"
    assert not os.path.exists(metadata_path), "Metadata file not deleted"
    
    # Test cleanup with no files
    assert not clean_report_index(), "Cleanup should return False when no files exist"