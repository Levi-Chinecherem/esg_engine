"""
This file contains unit tests for the settings module, ensuring configuration settings
are correctly defined and directories are created.

file path: esg_engine/tests/test_settings.py
"""

import pytest
import os
from config.settings import get_settings

def test_get_settings():
    """
    Tests that get_settings returns a valid configuration dictionary with expected keys
    and values, and that the output directory is created.
    """
    settings = get_settings()
    
    # Check dictionary structure
    assert "data_paths" in settings
    assert all(key in settings["data_paths"] for key in ["standards", "reports", "requirements", "output"])
    assert "resource_limits" in settings
    assert settings["resource_limits"]["local"]["ram_percent"] == 45.0
    assert settings["resource_limits"]["server"]["ram_percent"] == 80.0
    assert "model_params" in settings
    assert settings["model_params"]["sentence_transformer_model"] == "all-MiniLM-L6-v2"
    assert "monitoring" in settings
    assert settings["monitoring"]["update_interval"] == 1800
    
    # Check output directory exists
    assert os.path.exists(settings["data_paths"]["output"])