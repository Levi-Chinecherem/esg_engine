from pathlib import Path
import os
import logging
import faiss
from dotenv import load_dotenv

"""
Configuration settings for the Sustainability Reports Analyzer.
Defines paths, API keys, and resource limits for local PDF processing and analysis.

file path: config.py
"""

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Settings:
    """
    Holds configuration variables for the application.

    Attributes:
        PROJECT_NAME (str): Name of the project.
        OPENAI_API_KEY (str): API key for OpenAI services, loaded from environment.
        BASE_DIR (Path): Base directory of the project.
        INPUT_DIR (str): Directory for input PDF files.
        OUTPUT_DIR (str): Directory for output CSV files.
        CRITERIA_FOLDER (str): Directory for criteria CSV files.
        MAX_RESOURCE_USAGE (float): Maximum allowable system resource usage percentage for agent allocation.
    """
    PROJECT_NAME: str = "Sustainability Reports Analyzer"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    BASE_DIR: Path = Path(__file__).resolve().parent
    INPUT_DIR: str = str(BASE_DIR / "data" / "input")
    OUTPUT_DIR: str = str(BASE_DIR / "data" / "output")
    CRITERIA_FOLDER: str = str(BASE_DIR / "data" / "criteria")
    MAX_RESOURCE_USAGE: float = 80.0  # Default maximum resource usage percentage

    def __init__(self):
        """
        Initializes the settings and creates necessary directories.
        """
        os.makedirs(self.INPUT_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.CRITERIA_FOLDER, exist_ok=True)
        logger.info(f"Initialized directories: INPUT_DIR={self.INPUT_DIR}, OUTPUT_DIR={self.OUTPUT_DIR}, CRITERIA_FOLDER={self.CRITERIA_FOLDER}")

settings = Settings()

INDEX_DIR = Path("./indexes")
INDEX_DIR.mkdir(exist_ok=True)
INDEX_PATH = INDEX_DIR / "document_chunks.faiss"
DIMENSION = 384

# Check or create FAISS index with correct dimension
if INDEX_PATH.exists():
    faiss_index = faiss.read_index(str(INDEX_PATH))
    if faiss_index.d != DIMENSION:
        logger.warning(f"Existing FAISS index dimension {faiss_index.d} does not match expected {DIMENSION}. Recreating index.")
        faiss_index = faiss.IndexFlatL2(DIMENSION)
        faiss.write_index(faiss_index, str(INDEX_PATH))
    logger.info(f"Loaded existing FAISS index from {INDEX_PATH} with dimension {faiss_index.d}")
else:
    faiss_index = faiss.IndexFlatL2(DIMENSION)
    faiss.write_index(faiss_index, str(INDEX_PATH))
    logger.info(f"Created new FAISS index at {INDEX_PATH} with dimension {DIMENSION}")