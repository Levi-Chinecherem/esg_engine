import os
from dotenv import load_dotenv
from utils import logging

"""
File: esg_system/utils/config_loader.py
Role: Utility for loading configuration from .env file or environment variables.
Key Functionality:
- Loads configuration settings (e.g., file paths, Tesseract path, ChromaDB path).
- Validates Tesseract path existence.
- Provides helper functions to access configuration values.
- Logs loading success or errors for traceability.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

def load_config():
    """
    Load configuration from .env file or environment variables.
    
    Returns:
        dict: Configuration settings with defaults if not specified.
    
    Raises:
        FileNotFoundError: If .env file or Tesseract executable is specified but not found.
        ValueError: If critical configuration values are missing or invalid.
    """
    try:
        # Load .env file from project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        env_path = os.path.join(project_root, '.env')
        
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Loaded .env file from: {env_path}")
        else:
            logger.warning(f".env file not found at {env_path}. Using environment variables with defaults.")
        
        # Define default configuration
        config = {
            'STANDARDS_FILE': os.environ.get('STANDARDS_FILE', 'ifrs_s1.pdf'),
            'REQUIREMENTS_FILE': os.environ.get('REQUIREMENTS_FILE', 'UNCTAD_requirements.csv'),
            'TESSERACT_PATH': os.environ.get('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe'),
            'DB_PATH': os.environ.get('DB_PATH', os.path.join(project_root, 'chromadb'))
        }
        
        # Validate Tesseract path
        if not os.path.isfile(config['TESSERACT_PATH']):
            logger.error(f"Tesseract executable not found: {config['TESSERACT_PATH']}")
            raise FileNotFoundError(f"Tesseract executable not found: {config['TESSERACT_PATH']}")
        
        # Validate DB path
        if not os.path.exists(config['DB_PATH']):
            os.makedirs(config['DB_PATH'], exist_ok=True)
            logger.info(f"Created ChromaDB directory: {config['DB_PATH']}")
        
        logger.info("Configuration loaded successfully")
        return config
    
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        raise

def get_config_value(key, default=None):
    """
    Get a specific configuration value.
    
    Args:
        key (str): Configuration key (e.g., 'STANDARDS_FILE').
        default: Default value if key is not found.
    
    Returns:
        Value associated with the key, or default if not found.
    """
    try:
        config = load_config()
        value = config.get(key, default)
        logger.info(f"Retrieved config value for {key}: {value}")
        return value
    except Exception as e:
        logger.error(f"Error retrieving config value for {key}: {str(e)}")
        return default
