"""
Utility module for loading and caching NLTK WordNet corpus.

file path: esg_engine/utils/nltk_utils.py
"""

import logging
import os
import pickle
from datetime import datetime
import nltk
from config.settings import get_settings
import urllib.request
import ssl
import shutil

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "nltk_utils.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Cache configuration
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".esg_engine_cache")
CACHE_DURATION = 3600  # Cache for 1 hour (in seconds)
os.makedirs(CACHE_DIR, exist_ok=True)

def load_nltk_wordnet():
    """
    Loads or downloads the NLTK WordNet corpus, caching it to avoid repeated downloads.
    
    Returns:
        bool: True if WordNet is available, False if fallback to synonym dictionary is needed.
    """
    wordnet_cache_file = os.path.join(CACHE_DIR, "wordnet_cache.pkl")
    wordnet_dir = os.path.join(CACHE_DIR, "corpora", "wordnet")
    
    try:
        # Check cache validity
        if os.path.exists(wordnet_cache_file):
            with open(wordnet_cache_file, "rb") as f:
                cache_data = pickle.load(f)
            if datetime.now().timestamp() - cache_data["timestamp"] < CACHE_DURATION:
                if os.path.exists(wordnet_dir):
                    try:
                        from nltk.corpus import wordnet
                        nltk.data.path.append(CACHE_DIR)
                        wordnet.synsets("test")  # Test access
                        logging.info(f"Using cached NLTK WordNet corpus at {wordnet_dir}")
                        return True
                    except Exception as e:
                        logging.warning(f"WordNet corpus at {wordnet_dir} is corrupted: {str(e)}")
                        shutil.rmtree(wordnet_dir, ignore_errors=True)
                else:
                    logging.warning(f"WordNet cache file exists but directory {wordnet_dir} is missing")
        
        # Ensure write permissions
        if not os.access(CACHE_DIR, os.W_OK):
            raise PermissionError(f"No write permission for cache directory: {CACHE_DIR}")
        
        # Check disk space (WordNet is ~10 MB)
        stat = shutil.disk_usage(CACHE_DIR)
        if stat.free < 50 * 1024 * 1024:  # Less than 50 MB free
            raise OSError(f"Insufficient disk space in {CACHE_DIR}: {stat.free / 1024 / 1024:.2f} MB free")
        
        # Download WordNet with retries and SSL bypass for Windows
        logging.info("Attempting to download NLTK WordNet corpus")
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
                nltk.download('wordnet', download_dir=CACHE_DIR, quiet=True)
                if os.path.exists(wordnet_dir):
                    from nltk.corpus import wordnet
                    nltk.data.path.append(CACHE_DIR)
                    wordnet.synsets("test")  # Test access
                    with open(wordnet_cache_file, "wb") as f:
                        pickle.dump({"timestamp": datetime.now().timestamp()}, f)
                    logging.info(f"Downloaded and cached NLTK WordNet corpus to {wordnet_dir}")
                    return True
                else:
                    logging.warning(f"WordNet download attempt {attempt} failed: {wordnet_dir} not found")
            except Exception as e:
                logging.warning(f"WordNet download attempt {attempt} failed: {str(e)}")
                if attempt == max_retries:
                    raise FileNotFoundError(f"WordNet download failed after {max_retries} attempts: {wordnet_dir} not found")
    
    except Exception as e:
        logging.error(f"Failed to cache/load NLTK WordNet: {str(e)}. Falling back to synonym dictionary.")
        return False