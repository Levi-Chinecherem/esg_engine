"""
This module parses app-specific CSV requirement files for the Requirements RAG Database in the ESG Engine.
It reads CSVs from data/requirements/ (e.g., UNCTAD_requirements.csv), validates the format (category, criterion, description),
and embeds criteria/descriptions for FAISS indexing.

file path: esg_engine/rag/requirements_rag/parser.py
"""

import os
import pandas as pd
import logging
from utils.text_processing import tokenize_and_embed
from utils.vector_utils import initialize_index, add_to_index
from utils.resource_monitor import check_resources
from config.settings import get_settings

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "errors.log")
logging.basicConfig(filename=log_file, level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def parse_requirements():
    """
    Parses all CSVs in data/requirements/, validates format, and stores embeddings in a FAISS index.
    
    Returns:
        bool: True if parsing and indexing succeed, False otherwise.
    """
    # Check resource limits
    if not check_resources():
        logging.error("Resource usage exceeds 45% limit, aborting parsing")
        return False
    
    # Initialize paths
    requirements_dir = settings["data_paths"]["requirements"]
    index_path = os.path.join(requirements_dir, "index.faiss")
    metadata_path = os.path.join(requirements_dir, "metadata.pkl")
    dimension = 384  # Embedding dimension for all-MiniLM-L6-v2
    
    # Initialize FAISS index
    index = initialize_index(dimension, index_path)
    
    # Initialize metadata list
    all_metadata = []
    
    # Process each CSV
    for filename in os.listdir(requirements_dir):
        if filename.endswith(".csv"):
            file_path = os.path.join(requirements_dir, filename)
            try:
                # Read CSV
                df = pd.read_csv(file_path)
                
                # Validate CSV format
                expected_columns = ["category", "criterion", "description"]
                if not all(col in df.columns for col in expected_columns):
                    logging.error(f"Invalid CSV format in {filename}: Expected {expected_columns}")
                    continue
                
                # Prepare text for embedding (combine criterion and description)
                texts = df["criterion"] + " " + df["description"]
                text_data = [{"page_number": 1, "text": text} for text in texts]
                
                # Tokenize and embed
                results = tokenize_and_embed(text_data)
                if not results:
                    logging.warning(f"No embeddings generated for {filename}")
                    continue
                
                # Prepare embeddings and metadata
                embeddings = [res["embedding"] for res in results]
                metadata = [{
                    "app_name": filename,
                    "category": df.iloc[i]["category"],
                    "criterion": df.iloc[i]["criterion"],
                    "description": df.iloc[i]["description"],
                    "index": i
                } for i in range(len(df))]
                
                # Add to FAISS index
                add_to_index(index, embeddings, metadata, metadata_path, index_path)
                
                # Accumulate metadata
                all_metadata.extend(metadata)
                logging.info(f"Parsed and indexed {filename} with {len(metadata)} requirements")
                
            except Exception as e:
                logging.error(f"Failed to process {filename}: {str(e)}")
                continue
    
    # Save final metadata
    if all_metadata:
        with open(metadata_path, "wb") as f:
            import pickle
            pickle.dump(all_metadata, f)
            logging.info(f"Saved metadata with {len(all_metadata)} entries")
        return True
    return False