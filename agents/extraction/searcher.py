"""
This module searches the Reports RAG Database for criteria in the ESG Engine, retrieving
target sentences with context (before, after) and metadata for extraction.

file path: esg_engine/agents/extraction/searcher.py
"""

import logging
from config.settings import get_settings
from rag.reports_rag.searcher import search_report
import os

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "extraction.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_data(report_path, criterion):
    """
    Searches the Reports RAG for a single criterion, returning matches with context.
    
    Args:
        report_path (str): Path to the report PDF (e.g., btg-pactual.pdf).
        criterion (str): Requirement criterion to search for.
    
    Returns:
        dict: Dictionary with criterion and matches (metadata, context).
    """
    try:
        results = search_report([criterion], k=5)
        if not results:
            logging.warning(f"No matches found for criterion: {criterion}")
            return {"criterion": criterion, "matches": []}
        return results[0]
    
    except Exception as e:
        logging.error(f"Extraction failed for {criterion}: {str(e)}")
        return {"criterion": criterion, "matches": []}