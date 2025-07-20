"""
This module monitors data/standards/ and data/requirements/ for file changes in the ESG Engine,
notifying the Standards and Requirements RAG modules to update their indexes.

file path: esg_engine/agents/monitoring/file_watcher.py
"""

import logging
import os
from config.settings import get_settings
from utils.file_monitor import monitor_folder
from rag.standards_rag.updater import update_standards
from rag.requirements_rag.updater import update_requirements
import threading

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "monitor.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def watch_files():
    """
    Monitors data/standards/ and data/requirements/ for changes, triggering RAG updates.
    
    Returns:
        None
    """
    logging.info("Starting file monitoring")
    
    # Define callbacks
    def standards_callback(file_path):
        if file_path.endswith(".pdf"):
            logging.info(f"Detected change in standards: {file_path}")
            update_standards()
    
    def requirements_callback(file_path):
        if file_path.endswith(".csv"):
            logging.info(f"Detected change in requirements: {file_path}")
            update_requirements()
    
    # Start monitoring in separate threads
    standards_thread = threading.Thread(target=monitor_folder, args=(settings["data_paths"]["standards"], standards_callback), daemon=True)
    requirements_thread = threading.Thread(target=monitor_folder, args=(settings["data_paths"]["requirements"], requirements_callback), daemon=True)
    
    standards_thread.start()
    requirements_thread.start()
    
    try:
        standards_thread.join()
        requirements_thread.join()
    except KeyboardInterrupt:
        logging.info("Stopping file monitoring")