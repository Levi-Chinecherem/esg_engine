"""
This module initializes and populates a temporary FAISS index for the Reports RAG Database in the ESG Engine.
It processes a single ESG report PDF (e.g., btg-pactual.pdf), extracting text, tokenizing sentences,
generating embeddings, and storing them with metadata.

file path: esg_engine/rag/reports_rag/indexer.py
"""

import os
import logging
from utils.pdf_processing import extract_pdf_text
from utils.text_processing import tokenize_and_embed
from utils.vector_utils import initialize_index, add_to_index
from utils.resource_monitor import check_resources
from config.settings import get_settings

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "errors.log")
logging.basicConfig(filename=log_file, level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def index_report(report_path):
    """
    Initializes a temporary FAISS index and processes a single ESG report PDF, storing embeddings and metadata.
    
    Args:
        report_path (str): Path to the report PDF (e.g., data/reports/btg-pactual.pdf).
    
    Returns:
        bool: True if indexing succeeds, False otherwise.
    """
    # Validate report path
    if not os.path.exists(report_path) or not report_path.endswith(".pdf"):
        logging.error(f"Invalid report path: {report_path}")
        return False
    
    # Check resource limits
    if not check_resources():
        logging.error("Resource usage exceeds 45% limit, aborting indexing")
        return False
    
    # Initialize paths
    reports_dir = settings["data_paths"]["reports"]
    index_path = os.path.join(reports_dir, "index.faiss")
    metadata_path = os.path.join(reports_dir, "metadata.pkl")
    dimension = 384  # Embedding dimension for all-MiniLM-L6-v2
    
    # Initialize FAISS index
    index = initialize_index(dimension, index_path)
    
    try:
        # Extract text from PDF
        logging.info(f"Processing {report_path}")
        pages = extract_pdf_text(report_path)
        if not pages:
            logging.warning(f"No text extracted from {report_path}")
            return False
        
        # Tokenize and embed sentences
        results = tokenize_and_embed(pages)
        if not results:
            logging.warning(f"No embeddings generated for {report_path}")
            return False
        
        # Prepare embeddings and metadata
        embeddings = [res["embedding"] for res in results]
        metadata = [{
            "document_name": os.path.basename(report_path),
            "page_number": res["page_number"],
            "sentence_index": res["sentence_index"],
            "sentence": res["sentence"]
        } for res in results]
        
        # Add to FAISS index
        add_to_index(index, embeddings, metadata, metadata_path, index_path)
        logging.info(f"Indexed {report_path} with {len(metadata)} sentences")
        
        return True
    
    except Exception as e:
        logging.error(f"Failed to index {report_path}: {str(e)}")
        return False