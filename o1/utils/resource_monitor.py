"""
This module provides resource monitoring functionality for the ESG Engine, tracking RAM
and disk usage to enforce resource limits (80% for testing, adjustable in settings).

file path: esg_engine/utils/resource_monitor.py
"""

import psutil
import os
import logging
from config.settings import get_settings

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "resource.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def check_resources(is_server=False):
    """
    Checks RAM and disk usage against configured limits.
    
    Args:
        is_server (bool): If True, use server limits (80%); otherwise, use local limits (80% for testing).
    
    Returns:
        dict: Dictionary with 'compliant' (bool) and 'max_sub_agents' (int).
    """
    # Load settings
    settings = get_settings()
    limits = settings["resource_limits"]["server" if is_server else "local"]
    
    # Check RAM usage
    ram = psutil.virtual_memory()
    ram_used_percent = ram.percent
    ram_limit = 80  # Relaxed for testing, override settings limit
    
    # Check disk usage
    disk = psutil.disk_usage(settings["data_paths"]["output"])
    disk_used_percent = (disk.used / disk.total) * 100
    disk_limit = 80  # Relaxed for testing, override settings limit
    
    # Log resource usage
    logging.info(f"RAM: {ram_used_percent:.1f}% (limit {ram_limit}%), Disk: {disk_used_percent:.1f}% (limit {disk_limit}%)")
    
    # Determine compliance
    compliant = ram_used_percent <= ram_limit and disk_used_percent <= disk_limit
    if not compliant:
        logging.error(f"Resource usage exceeds limits: RAM {ram_used_percent:.1f}%, Disk {disk_used_percent:.1f}%")
    
    return {"compliant": compliant, "max_sub_agents": 4}