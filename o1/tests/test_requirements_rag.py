"""
This file contains unit tests for the Requirements RAG Database, testing parsing, searching,
and updating with real CSVs (UNCTAD_requirements.csv, UNEP_requirements.csv).

file path: esg_engine/tests/test_requirements_rag.py
"""

import pytest
import os
import pandas as pd
import time
from rag.requirements_rag.parser import parse_requirements
from rag.requirements_rag.searcher import search_requirements
from rag.requirements_rag.updater import update_requirements
from config.settings import get_settings
from utils.resource_monitor import check_resources

def test_parse_requirements(tmp_path):
    """
    Tests parsing and indexing of real CSVs.
    """
    settings = get_settings()
    requirements_dir = tmp_path / "requirements"
    requirements_dir.mkdir()
    settings["data_paths"]["requirements"] = str(requirements_dir)
    
    # Create a sample CSV mimicking expected format
    sample_csv = requirements_dir / "test_requirements.csv"
    df = pd.DataFrame({
        "category": ["Environment", "Governance"],
        "criterion": ["Emissions Reporting", "Board Diversity"],
        "description": ["Report annual carbon emissions.", "Ensure 30% diverse board members."]
    })
    df.to_csv(sample_csv, index=False)
    
    # Parse requirements and measure time
    start_time = time.time()
    assert parse_requirements(), "Parsing failed"
    assert time.time() - start_time < 10, "Parsing took longer than 10 seconds"
    
    # Verify index and metadata
    index_path = os.path.join(str(requirements_dir), "index.faiss")
    metadata_path = os.path.join(str(requirements_dir), "metadata.pkl")
    assert os.path.exists(index_path), "Index file not created"
    assert os.path.exists(metadata_path), "Metadata file not created"
    
    # Check metadata content
    with open(metadata_path, "rb") as f:
        import pickle
        metadata = pickle.load(f)
    assert len(metadata) == 2, "Incorrect number of requirements"
    assert any(m["app_name"] == "test_requirements.csv" for m in metadata)
    
    # Check resource usage
    assert check_resources(), "Resource usage exceeded 45% limit"

def test_search_requirements():
    """
    Tests searching requirements with and without app name filtering.
    """
    settings = get_settings()
    requirements_dir = settings["data_paths"]["requirements"]
    
    # Check if real CSVs exist
    real_csvs = ["UNCTAD_requirements.csv", "UNEP_requirements.csv"]
    if not all(os.path.exists(os.path.join(requirements_dir, f)) for f in real_csvs):
        pytest.skip("Real CSVs not found in data/requirements/")
    
    # Parse requirements
    assert parse_requirements(), "Parsing failed"
    
    # Test search with app filter
    query = "emissions reporting"
    start_time = time.time()
    results = search_requirements(query, app_name="UNCTAD_requirements.csv", k=2)
    assert time.time() - start_time < 0.5, "Search took longer than 0.5 seconds"
    assert isinstance(results, list), "Results should be a list"
    assert all(res["app_name"] == "UNCTAD_requirements.csv" for res in results)
    
    # Test full search (no filter)
    results = search_requirements(query, k=2)
    assert any(res["app_name"] in real_csvs for res in results)
    
    # Test empty query
    results = search_requirements("")
    assert results == [], "Empty query should return empty results"
    
    # Test missing index
    os.remove(os.path.join(requirements_dir, "index.faiss"))
    results = search_requirements(query)
    assert results == [], "Missing index should return empty results"

def test_update_requirements(tmp_path):
    """
    Tests updating the FAISS index when a new CSV is added.
    """
    settings = get_settings()
    requirements_dir = tmp_path / "requirements"
    requirements_dir.mkdir()
    settings["data_paths"]["requirements"] = str(requirements_dir)
    
    # Create initial CSV
    sample_csv = requirements_dir / "test_requirements.csv"
    df = pd.DataFrame({
        "category": ["Environment"],
        "criterion": ["Emissions Reporting"],
        "description": ["Report annual carbon emissions."]
    })
    df.to_csv(sample_csv, index=False)
    
    # Start updater in a separate thread
    import threading
    update_thread = threading.Thread(target=update_requirements, daemon=True)
    update_thread.start()
    
    # Simulate adding a new CSV
    new_csv = requirements_dir / "new_requirements.csv"
    new_df = pd.DataFrame({
        "category": ["Governance"],
        "criterion": ["Board Diversity"],
        "description": ["Ensure 30% diverse board members."]
    })
    new_df.to_csv(new_csv, index=False)
    
    # Wait for update
    time.sleep(2)
    
    # Verify index and metadata
    metadata_path = os.path.join(str(requirements_dir), "metadata.pkl")
    assert os.path.exists(metadata_path), "Metadata file not created"
    with open(metadata_path, "rb") as f:
        import pickle
        metadata = pickle.load(f)
    assert any(m["app_name"] == "new_requirements.csv" for m in metadata), "New CSV not indexed"