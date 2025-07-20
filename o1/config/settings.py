"""
This file defines configuration settings for the ESG Engine, including file paths, 
resource limits, and model parameters. It provides a centralized, reusable configuration 
accessible to all modules, ensuring consistency and ease of maintenance.

file path: esg_engine/config/settings.py
"""

import os

def get_settings():
    """
    Returns a dictionary of configuration settings for the ESG Engine.
    
    Returns:
        dict: Configuration settings including paths, resource limits, and model parameters.
    """
    # Define base directory for relative paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define configuration settings
    settings = {
        "data_paths": {
            "standards": os.path.join(base_dir, "data", "standards"),
            "reports": os.path.join(base_dir, "data", "reports"),
            "requirements": os.path.join(base_dir, "data", "requirements"),
            "output": os.path.join(base_dir, "data", "output")
        },
        "resource_limits": {
            "local": {
                "ram_percent": 45.0,  # Max 45% of available RAM
                "disk_percent": 45.0  # Max 45% of available disk
            },
            "server": {
                "ram_percent": 80.0,  # Max 80% of available RAM
                "disk_percent": 80.0  # Max 80% of available disk
            }
        },
        "model_params": {
            "sentence_transformer_model": "all-MiniLM-L6-v2",  # Embedding model
            "spacy_model": "en_core_web_sm"  # Tokenization model
        },
        "monitoring": {
            "update_interval": 1800  # 30 minutes in seconds for file polling
        }
    }
    
    # Ensure output directory exists
    os.makedirs(settings["data_paths"]["output"], exist_ok=True)
    
    return settings