"""
This file contains integration tests for the ESG Engine's main entry point, validating
end-to-end workflow with real data (btg-pactual.pdf, UNCTAD_requirements.csv, standards).

file path: esg_engine/tests/test_main.py
"""

import pytest
import os
import json
import time
import subprocess
from config.settings import get_settings

def test_main_integration(tmp_path):
    """
    Tests the end-to-end workflow via main.py with real data.
    """
    settings = get_settings()
    report_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    csv_path = os.path.join(settings["data_paths"]["requirements"], "UNCTAD_requirements.csv")
    standard_path = os.path.join(settings["data_paths"]["standards"], "ifrs_s1.pdf")
    
    if not (os.path.exists(report_path) and os.path.exists(csv_path) and os.path.exists(standard_path)):
        # Create sample files if real data is missing
        reports_dir = tmp_path / "reports"
        requirements_dir = tmp_path / "requirements"
        standards_dir = tmp_path / "standards"
        reports_dir.mkdir()
        requirements_dir.mkdir()
        standards_dir.mkdir()
        
        sample_report = reports_dir / "sample.pdf"
        sample_csv = requirements_dir / "sample.csv"
        sample_standard = standards_dir / "sample_standard.pdf"
        
        with open(sample_report, "w") as f:
            f.write("Sample ESG report")
        with open(sample_csv, "w") as f:
            f.write("category,criterion,description\nEnvironment,Emissions Reporting,Report emissions")
        with open(sample_standard, "w") as f:
            f.write("Sample standard")
        
        settings["data_paths"]["reports"] = str(reports_dir)
        settings["data_paths"]["requirements"] = str(requirements_dir)
        settings["data_paths"]["standards"] = str(standards_dir)
        report_path = str(sample_report)
        csv_path = str(sample_csv)
        standard_path = str(sample_standard)
    
    # Run main.py
    start_time = time.time()
    result = subprocess.run(
        ["python", "main.py", "--report", report_path, "--requirements", csv_path, "--standard", standard_path],
        capture_output=True, text=True
    )
    processing_time = time.time() - start_time
    
    # Verify execution
    assert result.returncode == 0, f"main.py failed: {result.stderr}"
    assert processing_time < 300, "Workflow took longer than 5 minutes"
    
    # Verify output
    output_path = os.path.join(settings["data_paths"]["output"], "results.json")
    assert os.path.exists(output_path), "Results JSON not created"
    
    with open(output_path, "r") as f:
        results = json.load(f)
    
    assert len(results) > 0, "No results generated"
    assert all(key in results[0] for key in [
        "category", "criterion", "extracted_sentences", "standard_info", "summary", "document_name", "processing_time"
    ]), "Results missing required fields"
    
    # Verify logs
    log_file = os.path.join(settings["data_paths"]["output"], "main.log")
    assert os.path.exists(log_file), "Main log not created"

def test_main_invalid_inputs():
    """
    Tests main.py with invalid inputs.
    """
    settings = get_settings()
    result = subprocess.run(
        ["python", "main.py", "--report", "invalid.pdf", "--requirements", "invalid.csv"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, "main.py crashed on invalid inputs"
    assert "not found" in result.stdout, "Expected error message for invalid inputs"
    
    log_file = os.path.join(settings["data_paths"]["output"], "main.log")
    assert os.path.exists(log_file), "Main log not created"
    with open(log_file, "r") as f:
        log_content = f.read()
    assert "Invalid input" in log_content, "Error not logged"

def test_main_resource_limit(tmp_path):
    """
    Tests main.py with resource limits exceeded (simulated).
    """
    settings = get_settings()
    report_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    csv_path = os.path.join(settings["data_paths"]["requirements"], "UNCTAD_requirements.csv")
    
    if not (os.path.exists(report_path) and os.path.exists(csv_path)):
        pytest.skip("Required files not found")
    
    # Simulate resource limit exceeded
    from utils.resource_monitor import check_resources
    original_check = check_resources
    def mock_check_resources():
        return False
    globals()["check_resources"] = mock_check_resources
    
    result = subprocess.run(
        ["python", "main.py", "--report", report_path, "--requirements", csv_path],
        capture_output=True, text=True
    )
    
    # Restore original function
    globals()["check_resources"] = original_check
    
    assert result.returncode == 0, "main.py crashed on resource limit"
    assert "Resource usage exceeds 45% limit" in result.stdout, "Expected resource limit error"