"""
This module provides file monitoring functionality for the ESG Engine, watching folders
for new or updated files using watchdog, with a polling fallback.

file path: esg_engine/utils/file_monitor.py
"""

import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config.settings import get_settings

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "monitor.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class FileEventHandler(FileSystemEventHandler):
    """
    Handles file system events, calling a callback on file changes.
    """
    def __init__(self, callback):
        self.callback = callback
    
    def on_created(self, event):
        if not event.is_directory:
            logging.info(f"File created: {event.src_path}")
            self.callback(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            logging.info(f"File modified: {event.src_path}")
            self.callback(event.src_path)

def monitor_folder(folder_path, callback):
    """
    Monitors a folder for new or updated files, triggering a callback.
    
    Args:
        folder_path (str): Path to the folder to monitor.
        callback (callable): Function to call on file changes.
    
    Returns:
        None
    """
    # Check if folder exists
    if not os.path.exists(folder_path):
        logging.error(f"Folder not found: {folder_path}")
        return
    
    # Initialize watchdog observer
    observer = Observer()
    event_handler = FileEventHandler(callback)
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()
    
    # Fallback polling every 30 minutes
    last_check = time.time()
    while True:
        current_time = time.time()
        if current_time - last_check >= settings["monitoring"]["update_interval"]:
            # Check for new files
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    callback(file_path)
            last_check = current_time
        time.sleep(1)