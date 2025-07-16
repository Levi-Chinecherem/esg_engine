"""
This module provides resource monitoring functionality for the ESG Engine, tracking RAM
and disk usage to enforce resource limits (45% local, 80% server).

file path: esg_engine/utils/resource_monitor.py
"""

import psutil
import os
from config.settings import get_settings

def check_resources(is_server=False):
    """
    Checks RAM and disk usage against configured limits.
    
    Args:
        is_server (bool): If True, use server limits (80%); otherwise, use local limits (45%).
    
    Returns:
        bool: True if within limits, False otherwise.
    """
    # Load settings
    settings = get_settings()
    limits = settings["resource_limits"]["server" if is_server else "local"]
    
    # Check RAM usage
    ram = psutil.virtual_memory()
    ram_used_percent = ram.percent
    ram_limit = limits["ram_percent"]
    
    # Check disk usage
    disk = psutil.disk_usage(settings["data_paths"]["output"])
    disk_used_percent = (disk.used / disk.total) * 100
    disk_limit = limits["disk_percent"]
    
    # Log resource usage
    import logging
    log_file = os.path.join(settings["data_paths"]["output"], "resource.log")
    logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info(f"RAM: {ram_used_percent:.1f}% (limit {ram_limit}%), Disk: {disk_used_percent:.1f}% (limit {disk_limit}%)")
    
    # Return True if within limits
    return ram_used_percent <= ram_limit and disk_used_percent <= disk_limit