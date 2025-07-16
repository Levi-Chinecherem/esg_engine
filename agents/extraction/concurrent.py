"""
This module manages concurrent searches for multiple criteria in the ESG Engine,
using the Reports RAG Database and respecting resource limits.

file path: esg_engine/agents/extraction/concurrent.py
"""

import logging
import concurrent.futures
from config.settings import get_settings
from .searcher import extract_data
from ..monitoring.resource_monitor import monitor_resources
import os

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "extraction.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def concurrent_extract(report_path, criteria):
    """
    Performs concurrent searches for multiple criteria, respecting resource limits.
    
    Args:
        report_path (str): Path to the report PDF (e.g., btg-pactual.pdf).
        criteria (list): List of requirement criteria to search for.
    
    Returns:
        list: List of dictionaries with criterion and matches.
    """
    # Check resource limits and get max sub-agents
    resource_info = monitor_resources()
    if not resource_info["compliant"]:
        logging.error("Resource usage exceeds 45% limit, aborting extraction")
        return []
    
    max_sub_agents = resource_info["max_sub_agents"]
    
    # Perform concurrent searches
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_sub_agents) as executor:
        future_to_criterion = {executor.submit(extract_data, report_path, criterion): criterion for criterion in criteria}
        for future in concurrent.futures.as_completed(future_to_criterion):
            results.append(future.result())
    
    return results