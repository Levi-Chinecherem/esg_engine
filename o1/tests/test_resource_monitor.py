"""
This file contains unit tests for the resource_monitor module, ensuring resource usage
is correctly checked against limits during btg-pactual.pdf processing.

file path: esg_engine/tests/test_resource_monitor.py
"""

import pytest
import os
from utils.resource_monitor import check_resources
from utils.pdf_processing import extract_pdf_text
from config.settings import get_settings

def test_check_resources_btg_pactual():
    """
    Tests resource monitoring during btg-pactual.pdf processing.
    """
    settings = get_settings()
    pdf_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    
    if not os.path.exists(pdf_path):
        pytest.skip("btg-pactual.pdf not found in data/reports/")
    
    # Process PDF to simulate load
    extract_pdf_text(pdf_path)
    
    # Check resources
    assert check_resources(is_server=False), "Resource usage exceeded 45% limit"