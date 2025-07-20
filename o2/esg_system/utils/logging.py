import logging
import os
from datetime import datetime

"""
File: esg_system/utils/logging.py
Role: Configures logging for the ESG Compliance Verification System.
Key Functionality:
- Sets up logging to file (logs/esg_system.log) and console.
- Formats logs with timestamp, level, and message.
- Ensures consistent logging across all modules.
"""

def setup_logger(name):
    """
    Set up a logger with file and console handlers.
    
    Args:
        name (str): Name of the logger (typically __name__).
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'esg_system.log')
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"Logger initialized for {name}")
    return logger
