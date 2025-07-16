"""
This module initializes and populates a FAISS index for the Standards RAG Database in the ESG Engine.
It processes all PDFs in data/standards/ (e.g., ifrs_s1.pdf, ifrs_s2.pdf, ESRS_2.pdf), extracting text,
tokenizing sentences, generating embeddings, and storing them with metadata.

file path: esg_engine/rag/standards_rag/indexer.py
"""

import os
import logging
from utils.pdf_processing import extract_pdf_text
from utils.text_processing import tokenize_and_embed
from utils.vector_utils import initialize_index, add_to_index
from config.settings import get_settings

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "errors.log")
logging.basicConfig(filename=log_file, level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def index_standards():
    """
    Initializes a FAISS index and processes all PDFs in data/standards/, storing embeddings and metadata.
    
    Returns:
        None
    
    Raises:
        Exception: Errors are logged by pdf_processing.py; invalid PDFs are skipped.
    """
    # Load settings
    standards_dir = settings["data_paths"]["standards"]
    index_path = os.path.join(standards_dir, "index.faiss")
    metadata_path = os.path.join(standards_dir, "metadata.pkl")
    dimension = 384  # Embedding dimension for all-MiniLM-L6-v2
    
    # Initialize FAISS index
    index = initialize_index(dimension, index_path)
    
    # Initialize metadata list
    all_metadata = []
    
    # Process each PDF in standards directory
    for filename in os.listdir(standards_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(standards_dir, filename)
            try:
                # Extract text from PDF
                logging.info(f"Processing {filename}")
                pages = extract_pdf_text(file_path)
                if not pages:
                    logging.warning(f"No text extracted from {filename}")
                    continue
                
                # Tokenize and embed sentences
                results = tokenize_and_embed(pages)
                if not results:
                    logging.warning(f"No embeddings generated for {filename}")
                    continue
                
                # Prepare embeddings and metadata
                embeddings = [res["embedding"] for res in results]
                metadata = [{
                    "document_name": filename,
                    "page_number": res["page_number"],
                    "sentence_index": res["sentence_index"],
                    "sentence": res["sentence"]
                } for res in results]
                
                # Add to FAISS index
                add_to_index(index, embeddings, metadata, metadata_path, index_path)
                
                # Accumulate metadata
                all_metadata.extend(metadata)
                logging.info(f"Indexed {filename} with {len(metadata)} sentences")
                
            except Exception as e:
                # Errors are logged in pdf_processing.py; skip problematic files
                logging.error(f"Failed to process {filename}: {str(e)}")
                continue
    
    # Save final metadata
    if all_metadata:
        with open(metadata_path, "wb") as f:
            import pickle
            pickle.dump(all_metadata, f)
            logging.info(f"Saved metadata with {len(all_metadata)} entries")