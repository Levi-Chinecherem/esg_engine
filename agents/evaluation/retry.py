"""
This module retries failed extractions for the ESG Engine, attempting one retry
and flagging unresolved issues.

file path: esg_engine/agents/evaluation/retry.py
"""

import logging
from config.settings import get_settings
from ..extraction.searcher import extract_data
import os

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "evaluation.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def retry_extraction(report_path, extraction):
    """
    Retries failed extractions once, flagging unresolved issues.
    
    Args:
        report_path (str): Path to the report PDF (e.g., btg-pactual.pdf).
        extraction (dict): Original extraction with criterion and matches.
    
    Returns:
        dict: Updated extraction with matches or flagged failure.
    """
    criterion = extraction["criterion"]
    if extraction.get("matches"):
        return extraction
    
    try:
        logging.info(f"Retrying extraction for criterion: {criterion}")
        result = extract_data(report_path, criterion)
        if result.get("matches"):
            logging.info(f"Retry successful for {criterion}")
            return result
        logging.warning(f"Retry failed for {criterion}")
        return {"criterion": criterion, "matches": [], "status": "Failed"}
    
    except Exception as e:
        logging.error(f"Retry failed for {criterion}: {str(e)}")
        return {"criterion": criterion, "matches": [], "status": "Failed"}