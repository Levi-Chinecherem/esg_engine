"""
This module provides file monitoring functionality for the ESG Engine, using watchdog to detect
file changes in specified directories.

file path: esg_engine/utils/file_monitor.py
"""

import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config.settings import get_settings

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "monitor.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class FileMonitorHandler(FileSystemEventHandler):
    """
    Handles file system events by calling the provided callback function.
    """
    def __init__(self, callback):
        self.callback = callback
    
    def on_created(self, event):
        if not event.is_directory:
            logging.info(f"Detected new file: {event.src_path}")
            self.callback(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            logging.info(f"Detected modified file: {event.src_path}")
            self.callback(event.src_path)

def monitor_folder(folder_path, callback):
    """
    Monitors a folder for file creation or modification events, triggering the callback.
    
    Args:
        folder_path (str): Path to the folder to monitor.
        callback (callable): Function to call when a file event occurs.
    
    Returns:
        None
    """
    if not os.path.exists(folder_path):
        logging.error(f"Folder not found: {folder_path}")
        os.makedirs(folder_path)
        logging.info(f"Created folder: {folder_path}")
    
    observer = Observer()
    event_handler = FileMonitorHandler(callback)
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()
    
    try:
        while observer.is_alive():
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()