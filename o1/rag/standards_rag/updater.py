"""
This module provides update functionality for the Standards RAG Database in the ESG Engine.
It monitors data/standards/ for new or updated PDFs (e.g., ifrs_s1.pdf) and refreshes
the FAISS index every 30 minutes or on file changes.

file path: esg_engine/rag/standards_rag/updater.py
"""

import logging
import os
from config.settings import get_settings
from utils.file_monitor import monitor_folder
from .indexer import index_standards
import threading

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "standards_update.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def update_standards():
    """
    Monitors data/standards/ for changes and refreshes the FAISS index.
    
    Returns:
        None
    """
    # Initial indexing
    if index_standards():
        logging.info("Initial standards indexing completed")
    else:
        logging.warning("Initial standards indexing failed")
    
    # Define callback to reindex standards
    def callback(file_path):
        if file_path.endswith(".pdf"):
            logging.info(f"Detected change in {file_path}, reindexing standards")
            if index_standards():
                logging.info(f"Successfully reindexed standards for {file_path}")
            else:
                logging.warning(f"Failed to reindex standards for {file_path}")
    
    # Monitor standards directory
    standards_dir = settings["data_paths"]["standards"]
    monitor_thread = threading.Thread(target=monitor_folder, args=(standards_dir, callback), daemon=True)
    monitor_thread.start()
    
    try:
        monitor_thread.join()
    except KeyboardInterrupt:
        logging.info("Stopping standards monitoring")