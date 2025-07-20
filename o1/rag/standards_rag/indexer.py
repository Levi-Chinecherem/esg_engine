"""
This module initializes and populates a FAISS index for the Standards RAG Database in the ESG Engine.
It processes all PDFs in data/standards/ (e.g., ifrs_s1.pdf, ifrs_s2.pdf, ESRS_2.pdf), extracting text,
tokenizing sentences, generating embeddings, and storing them with metadata.

file path: esg_engine/rag/standards_rag/indexer.py
"""

import os
import logging
import pickle
import csv
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
    Initializes a FAISS index and processes all PDFs in data/standards/ and requirements in data/requirements/,
    storing embeddings, metadata, and raw texts. Skips processing if cache and index files exist.
    
    Returns:
        bool: True if index exists or is created successfully, False otherwise.
    
    Raises:
        Exception: Errors are logged by pdf_processing.py; invalid files are skipped.
    """
    # Load settings
    standards_dir = settings["data_paths"]["standards"]
    requirements_dir = settings["data_paths"].get("requirements", standards_dir)
    index_path = os.path.join(standards_dir, "index.faiss")
    metadata_path = os.path.join(standards_dir, "metadata.pkl")
    text_cache_path = os.path.join(standards_dir, "texts_cache.pkl")
    dimension = 384
    
    # Check if index and cache already exist
    if os.path.exists(index_path) and os.path.exists(metadata_path) and os.path.exists(text_cache_path):
        logging.info(f"Found existing index and cache at {index_path}, {metadata_path}, {text_cache_path}. Skipping indexing.")
        return True
    
    # Initialize FAISS index
    index = initialize_index(dimension, index_path)
    
    # Initialize metadata and text cache
    all_metadata = []
    all_texts = {"standards": {}, "requirements": {}}
    success = False
    
    # Process standards PDFs
    for filename in os.listdir(standards_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(standards_dir, filename)
            try:
                logging.info(f"Processing standard {filename}")
                pages = extract_pdf_text(file_path)
                if not pages:
                    logging.warning(f"No text extracted from {filename}")
                    continue
                
                # Cache page texts
                page_texts = {page['page_number']: page['text'] for page in pages}
                all_texts["standards"][filename] = page_texts
                
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
                    "sentence": res["sentence"],
                    "type": "standard"
                } for res in results]
                
                # Add to FAISS index
                add_to_index(index, embeddings, metadata, metadata_path, index_path)
                
                # Accumulate metadata
                all_metadata.extend(metadata)
                logging.info(f"Indexed {filename} with {len(metadata)} sentences")
                success = True
                
            except Exception as e:
                logging.error(f"Failed to process {filename}: {str(e)}")
                continue
    
    # Process requirements (CSV or text)
    for filename in os.listdir(requirements_dir):
        if filename.endswith(".csv"):
            file_path = os.path.join(requirements_dir, filename)
            try:
                logging.info(f"Processing requirements {filename}")
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    requirements = list(reader)
                
                # Cache requirements text
                req_texts = {i: f"{row['criterion']}: {row.get('description', '')}" for i, row in enumerate(requirements)}
                all_texts["requirements"][filename] = req_texts
                
                # Tokenize and embed requirements
                results = tokenize_and_embed([
                    {"page_number": i, "text": text} for i, text in req_texts.items()
                ])
                if not results:
                    logging.warning(f"No embeddings generated for {filename}")
                    continue
                
                # Prepare embeddings and metadata
                embeddings = [res["embedding"] for res in results]
                metadata = [{
                    "document_name": filename,
                    "page_number": res["page_number"],
                    "sentence_index": res["sentence_index"],
                    "sentence": res["sentence"],
                    "type": "requirement"
                } for res in results]
                
                # Add to FAISS index
                add_to_index(index, embeddings, metadata, metadata_path, index_path)
                
                # Accumulate metadata
                all_metadata.extend(metadata)
                logging.info(f"Indexed {filename} with {len(metadata)} requirements")
                success = True
                
            except Exception as e:
                logging.error(f"Failed to process {filename}: {str(e)}")
                continue
    
    # Save final metadata and texts
    if all_metadata:
        with open(metadata_path, "wb") as f:
            pickle.dump(all_metadata, f)
            logging.info(f"Saved metadata with {len(all_metadata)} entries")
    
    if all_texts["standards"] or all_texts["requirements"]:
        with open(text_cache_path, "wb") as f:
            pickle.dump(all_texts, f)
            logging.info(f"Saved texts for {len(all_texts['standards'])} standards and {len(all_texts['requirements'])} requirements")
    
    return success