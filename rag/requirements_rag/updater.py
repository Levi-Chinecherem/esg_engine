"""
This module provides update functionality for the Requirements RAG Database in the ESG Engine.
It monitors data/requirements/ for new or updated CSVs (e.g., UNCTAD_requirements.csv) and refreshes
the FAISS index every 30 minutes or on file changes.

file path: esg_engine/rag/requirements_rag/updater.py
"""

import logging
from config.settings import get_settings
from utils.file_monitor import monitor_folder
from .parser import parse_requirements
import os

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "requirements_update.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def update_requirements():
    """
    Monitors data/requirements/ for changes and refreshes the FAISS index.
    
    Returns:
        None
    """
    # Define callback to reparse requirements
    def callback(file_path):
        if file_path.endswith(".csv"):
            logging.info(f"Detected change in {file_path}, reindexing requirements")
            parse_requirements()
    
    # Monitor requirements directory
    requirements_dir = settings["data_paths"]["requirements"]
    monitor_folder(requirements_dir, callback)