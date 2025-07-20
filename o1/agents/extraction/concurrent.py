"""
This module manages concurrent extraction for multiple criteria in the ESG Engine,
using threading to speed up the process while respecting resource limits.

file path: esg_engine/agents/extraction/concurrent.py
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from config.settings import get_settings
from .searcher import extract_data
from agents.monitoring.resource_monitor import monitor_resources
import os

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "extraction.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def concurrent_extract(report_path, criteria, criteria_descriptions, report_page_texts, standards_texts):
    """
    Concurrently extracts data for multiple criteria using threading.

    Args:
        report_path (str): Path to the report PDF.
        criteria (list): List of criteria to search for.
        criteria_descriptions (dict): Dictionary mapping criteria to descriptions.
        report_page_texts (dict): Cached report texts {page_number: text}.
        standards_texts (dict): Cached standards texts {filename: {page_number: text}}.

    Returns:
        list: List of extraction results for each criterion.
    """
    resource_info = monitor_resources()
    max_workers = resource_info["max_sub_agents"]
    logging.info(f"Using {max_workers} concurrent workers for extraction with cached report texts")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            lambda c: extract_data(report_path, c, criteria_descriptions.get(c), report_page_texts),
            criteria
        ))
    logging.info(f"Completed concurrent extraction for {len(criteria)} criteria")
    return results