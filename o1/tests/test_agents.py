"""
This file contains unit tests for the ESG Engine's agent system, testing coordination,
workflow, monitoring, extraction, evaluation, and summarization with real data (btg-pactual.pdf, UNCTAD_requirements.csv).

file path: esg_engine/tests/test_agents.py
"""

import pytest
import os
import json
import time
from agents.superbrain.coordinator import initialize_system
from agents.superbrain.workflow import execute_workflow
from agents.monitoring.resource_monitor import monitor_resources
from agents.monitoring.file_watcher import watch_files
from agents.extraction.searcher import extract_data
from agents.extraction.concurrent import concurrent_extract
from agents.evaluation.validator import validate_data
from agents.evaluation.retry import retry_extraction
from agents.summarization.summarizer import generate_summary
from config.settings import get_settings

def test_initialize_system(tmp_path):
    """
    Tests system initialization with a report.
    """
    settings = get_settings()
    report_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    if not os.path.exists(report_path):
        pytest.skip("btg-pactual.pdf not found")
    
    agents = initialize_system(report_path)
    assert agents, "Initialization failed"
    assert "standards_rag" in agents
    assert "reports_rag" in agents
    assert "requirements_rag" in agents

def test_workflow(tmp_path):
    """
    Tests end-to-end workflow with real data.
    """
    settings = get_settings()
    report_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    csv_path = os.path.join(settings["data_paths"]["requirements"], "UNCTAD_requirements.csv")
    
    if not (os.path.exists(report_path) and os.path.exists(csv_path)):
        pytest.skip("Required files not found")
    
    start_time = time.time()
    assert execute_workflow(report_path, csv_path, standard_filter="ifrs_s1.pdf"), "Workflow failed"
    assert time.time() - start_time < 300, "Workflow took longer than 5 minutes"
    
    output_path = os.path.join(settings["data_paths"]["output"], "results.json")
    assert os.path.exists(output_path), "Results JSON not created"
    
    with open(output_path, "r") as f:
        results = json.load(f)
    assert len(results) > 0, "No results generated"
    assert all(key in results[0] for key in ["category", "criterion", "extracted_sentences", "standard_info", "summary", "document_name", "processing_time"])

def test_resource_monitor():
    """
    Tests resource monitoring.
    """
    result = monitor_resources()
    assert result["compliant"], "Resource usage exceeds 45% limit"
    assert isinstance(result["max_sub_agents"], int)

def test_file_watcher(tmp_path):
    """
    Tests file monitoring for standards and requirements.
    """
    settings = get_settings()
    standards_dir = tmp_path / "standards"
    requirements_dir = tmp_path / "requirements"
    standards_dir.mkdir()
    requirements_dir.mkdir()
    settings["data_paths"]["standards"] = str(standards_dir)
    settings["data_paths"]["requirements"] = str(requirements_dir)
    
    import threading
    watch_thread = threading.Thread(target=watch_files, daemon=True)
    watch_thread.start()
    
    # Simulate file creation
    with open(standards_dir / "test.pdf", "w") as f:
        f.write("test")
    with open(requirements_dir / "test.csv", "w") as f:
        f.write("category,criterion,description\ntest,test,test")
    
    time.sleep(2)  # Wait for detection
    log_file = os.path.join(settings["data_paths"]["output"], "monitor.log")
    assert os.path.exists(log_file), "Monitor log not created"

def test_extraction(tmp_path):
    """
    Tests extraction for a single criterion.
    """
    settings = get_settings()
    report_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    if not os.path.exists(report_path):
        pytest.skip("btg-pactual.pdf not found")
    
    from rag.reports_rag.indexer import index_report
    assert index_report(report_path), "Indexing failed"
    
    result = extract_data(report_path, "emissions reporting")
    assert isinstance(result, dict)
    assert "criterion" in result
    assert "matches" in result

def test_concurrent_extraction(tmp_path):
    """
    Tests concurrent extraction for multiple criteria.
    """
    settings = get_settings()
    report_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    if not os.path.exists(report_path):
        pytest.skip("btg-pactual.pdf not found")
    
    from rag.reports_rag.indexer import index_report
    assert index_report(report_path), "Indexing failed"
    
    criteria = ["emissions reporting", "governance"]
    start_time = time.time()
    results = concurrent_extract(report_path, criteria)
    assert time.time() - start_time < 1, "Concurrent extraction took longer than 1 second"
    assert len(results) == len(criteria)
    assert all("criterion" in res for res in results)

def test_validation():
    """
    Tests validation of extracted data.
    """
    extraction = {"criterion": "emissions reporting", "matches": [{"sentence": "Test emission data"}]}
    result = validate_data(extraction, standard_filter="ifrs_s1.pdf")
    assert isinstance(result, dict)
    assert "criterion" in result
    assert "standard_matches" in result
    assert "compliance" in result

def test_retry_extraction(tmp_path):
    """
    Tests retry logic for failed extractions.
    """
    settings = get_settings()
    report_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    if not os.path.exists(report_path):
        pytest.skip("btg-pactual.pdf not found")
    
    extraction = {"criterion": "invalid", "matches": []}
    result = retry_extraction(report_path, extraction)
    assert isinstance(result, dict)
    assert "criterion" in result
    assert "matches" in result

def test_summarization():
    """
    Tests summary generation.
    """
    extraction = {"criterion": "emissions reporting", "matches": [{"sentence": "Test emission data"}]}
    validation = {"criterion": "emissions reporting", "standard_matches": [], "compliance": "Compliant"}
    requirement = {"category": "Environment", "criterion": "emissions reporting", "description": "Report emissions"}
    summary = generate_summary(extraction, validation, requirement)
    assert isinstance(summary, str)
    assert "emissions reporting" in summary