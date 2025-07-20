"""
This file contains unit tests for the file_monitor module, ensuring folder monitoring
and callback triggering work correctly with btg-pactual.pdf.

file path: esg_engine/tests/test_file_monitor.py
"""

import pytest
import os
import time
from utils.file_monitor import monitor_folder
from config.settings import get_settings

def test_monitor_folder(tmp_path):
    """
    Tests folder monitoring by simulating a file creation in data/reports/.
    """
    settings = get_settings()
    folder_path = settings["data_paths"]["reports"]
    
    called = []
    def callback(path):
        called.append(path)
    
    # Start monitoring in a separate thread
    import threading
    monitor_thread = threading.Thread(target=monitor_folder, args=(folder_path, callback), daemon=True)
    monitor_thread.start()
    
    # Simulate copying btg-pactual.pdf
    test_file = os.path.join(folder_path, "btg-pactual.pdf")
    if os.path.exists(test_file):
        os.rename(test_file, test_file + ".bak")  # Move temporarily
    with open(test_file, "w") as f:
        f.write("test")  # Simulate file creation
    
    # Wait for event
    time.sleep(1)
    
    assert len(called) > 0
    assert test_file in called
    
    # Cleanup
    os.remove(test_file)
    if os.path.exists(test_file + ".bak"):
        os.rename(test_file + ".bak", test_file)