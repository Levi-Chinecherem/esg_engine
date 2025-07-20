"""
This module monitors resource usage for the ESG Engine's agent system, enforcing 45% local
or 80% server limits and advising on concurrency limits for sub-agents.

file path: esg_engine/agents/monitoring/resource_monitor.py
"""

import logging
import psutil
from config.settings import get_settings
from utils.resource_monitor import check_resources
import os

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "resource.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def monitor_resources():
    """
    Checks resource usage and advises on maximum sub-agents for concurrent processing.
    
    Returns:
        dict: Contains resource compliance (bool) and max_sub_agents (int).
    """
    # Check resource limits
    is_compliant = check_resources()
    
    # Calculate max sub-agents based on available RAM
    available_memory = psutil.virtual_memory().available / (1024 ** 3)  # Convert to GB
    max_sub_agents = min(int(available_memory // 0.5), 10)  # Assume 0.5GB per sub-agent, cap at 10
    
    logging.info(f"Resource check: compliant={is_compliant}, max_sub_agents={max_sub_agents}")
    return {"compliant": is_compliant, "max_sub_agents": max_sub_agents}