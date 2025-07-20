"""
This module provides update functionality for the Requirements RAG Database in the ESG Engine.
It monitors data/requirements/ for new or updated CSVs (e.g., UNCTAD_requirements.csv) and refreshes
the FAISS index every 30 minutes or on file changes.

file path: esg_engine/rag/requirements_rag/updater.py
"""

import logging
import os
from config.settings import get_settings
from utils.file_monitor import monitor_folder
from .parser import parse_requirements
from utils.resource_monitor import check_resources

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "workflow.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def update_requirements():
    """
    Monitors data/requirements/ for changes and refreshes the FAISS index.

    Returns:
        bool: True if initial parse succeeds, False otherwise.
    """
    try:
        # Check resources
        if not check_resources()["compliant"]:
            logging.error("Resource usage exceeds limit, aborting requirements update")
            return False

        # Validate requirements directory
        requirements_dir = settings["data_paths"]["requirements"]
        if not os.path.exists(requirements_dir):
            logging.error(f"Requirements directory {requirements_dir} does not exist")
            return False

        # Initial parse
        logging.info("Starting initial requirements parse")
        if not parse_requirements():
            logging.error("Initial requirements parse failed")
            return False
        logging.info("Initial requirements parse completed successfully")

        # Define callback to reparse requirements
        def callback(file_path):
            if file_path.endswith(".csv"):
                logging.info(f"Detected change in {file_path}, reindexing requirements")
                if not parse_requirements():
                    logging.error(f"Failed to reindex requirements for {file_path}")
                else:
                    logging.info(f"Successfully reindexed requirements for {file_path}")

        # Monitor requirements directory
        logging.info(f"Starting folder monitoring for {requirements_dir}")
        monitor_folder(requirements_dir, callback)
        return True

    except Exception as e:
        logging.error(f"Requirements update failed: {str(e)}", exc_info=True)
        return False