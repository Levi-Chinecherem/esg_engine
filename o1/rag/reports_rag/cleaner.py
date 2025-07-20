"""
This module provides cleanup functionality for the Reports RAG Database in the ESG Engine.
It deletes the temporary FAISS index and metadata after processing a report, ensuring no residual files remain.

file path: esg_engine/rag/reports_rag/cleaner.py
"""

import os
import logging
from config.settings import get_settings

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "cleanup.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def clean_report_index():
    """
    Deletes the temporary FAISS index and metadata files from data/reports/.
    
    Returns:
        bool: True if cleanup succeeds, False if no files were found.
    """
    # Define paths
    reports_dir = settings["data_paths"]["reports"]
    index_path = os.path.join(reports_dir, "temp_index.faiss")
    metadata_path = os.path.join(reports_dir, "temp_metadata.pkl")
    
    # Track cleanup success
    cleaned = False
    
    # Remove index file
    if os.path.exists(index_path):
        try:
            os.remove(index_path)
            logging.info(f"Deleted temporary index: {index_path}")
            cleaned = True
        except Exception as e:
            logging.error(f"Failed to delete {index_path}: {str(e)}")
    
    # Remove metadata file
    if os.path.exists(metadata_path):
        try:
            os.remove(metadata_path)
            logging.info(f"Deleted temporary metadata: {metadata_path}")
            cleaned = True
        except Exception as e:
            logging.error(f"Failed to delete {metadata_path}: {str(e)}")
    
    return cleaned