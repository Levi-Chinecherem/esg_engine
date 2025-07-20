"""
This module parses and indexes requirements from CSV files for the Requirements RAG Database in the ESG Engine.
It processes CSVs in the data/requirements/ directory, validates their structure (category, criterion, description),
and generates embeddings for criteria and descriptions using the all-MiniLM-L6-v2 model. The embeddings are stored
in a FAISS index for efficient retrieval. Logging is output to data/output/workflow.log with detailed error handling.

file path: esg_engine/rag/requirements_rag/parser.py
"""

import os
import pandas as pd
import pickle
import logging
import numpy as np
import re
from config.settings import get_settings
from utils.text_processing import tokenize_and_embed
from utils.vector_utils import initialize_index, add_to_index
from utils.resource_monitor import check_resources
from sentence_transformers import SentenceTransformer

# Configure logging
settings = get_settings()
output_dir = settings["data_paths"]["output"]
log_file = os.path.join(output_dir, "workflow.log")
os.makedirs(output_dir, exist_ok=True)

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("Logging initialized successfully")

# Load SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')
logging.info("Loaded SentenceTransformer: all-MiniLM-L6-v2")

def parse_requirements() -> bool:
    """
    Parses all CSVs in data/requirements/, generates embeddings in batches, and updates the FAISS index.
    Validates CSV structure and ensures robust indexing with metadata storage.

    Returns:
        bool: True if successful, False if resource limits exceeded or no valid data.
    """
    try:
        requirements_dir = settings["data_paths"]["requirements"]
        index_path = os.path.join(requirements_dir, "index.faiss")
        metadata_path = os.path.join(requirements_dir, "metadata.pkl")
        dimension = 384  # Embedding dimension for all-MiniLM-L6-v2
        batch_size = 50  # Process rows in batches

        # Check resources
        resources = check_resources()
        ram_usage = resources.get("ram_usage", "N/A")
        disk_usage = resources.get("disk_usage", "N/A")
        compliant = resources.get("compliant", False)
        logging.info(f"RAM: {ram_usage}% (limit 45%), Disk: {disk_usage}% (limit 45%)")
        if not compliant:
            logging.error("Resource usage too high (RAM or disk exceeds 45%)")
            return False
        if ram_usage == "N/A" or disk_usage == "N/A":
            logging.warning("Resource check returned incomplete data, proceeding with caution")

        if not os.path.exists(requirements_dir):
            logging.error(f"Requirements directory missing: {requirements_dir}")
            return False

        index = initialize_index(dimension, index_path)
        if index is None:
            logging.error("Failed to initialize FAISS index")
            return False

        all_metadata = []
        # Regex pattern for meaningful numerical values
        pattern = r"([\$€£R\$][\d,.]+(?:\s*(?:billion|million|thousand|tCO2e|%|tons|litres|m³|kWh|MWh|hours|employees)))\b"

        for filename in os.listdir(requirements_dir):
            if filename.endswith(".csv"):
                file_path = os.path.join(requirements_dir, filename)
                try:
                    logging.info(f"Processing {filename}")
                    df = pd.read_csv(file_path)
                    if df.empty:
                        logging.warning(f"Empty CSV: {filename}")
                        continue

                    # Validate required columns
                    required_columns = ['category', 'criterion', 'description']
                    if not all(col in df.columns for col in required_columns):
                        logging.warning(f"Missing required columns in {filename}: {set(required_columns) - set(df.columns)}")
                        continue

                    # Validate rows
                    initial_rows = len(df)
                    df = df.dropna(subset=['criterion']).reset_index(drop=True)
                    if df.empty:
                        logging.warning(f"No valid rows in {filename} after dropping empty criteria")
                        continue
                    if len(df) < initial_rows:
                        logging.warning(f"Dropped {initial_rows - len(df)} rows with empty criteria in {filename}")

                    logging.info(f"Rows in {filename}: {len(df)}")

                    # Process rows in batches
                    for batch_start in range(0, len(df), batch_size):
                        batch_df = df.iloc[batch_start:batch_start + batch_size]
                        texts = []
                        valid_rows = []
                        for idx, row in batch_df.iterrows():
                            criterion = row.get('criterion', '')
                            description = row.get('description', '')
                            text = f"{criterion} {description}" if pd.notna(description) else criterion
                            if pd.notna(text) and text.strip():
                                texts.append(text)
                                valid_rows.append(idx)
                                # Extract numerical values (no logging)
                                regex_match = re.search(pattern, text, re.IGNORECASE)
                                value = regex_match.group(1) if regex_match else "None"
                            else:
                                logging.warning(f"Empty or invalid text for row {idx} in {filename}: {row.to_dict()}")

                        if not texts:
                            logging.warning(f"No valid texts in batch {batch_start} of {filename}")
                            continue

                        # Tokenize and embed batch
                        results = tokenize_and_embed([{"page_number": 0, "text": text} for text in texts])
                        if not results:
                            logging.warning(f"No embeddings generated for batch {batch_start} of {filename}")
                            continue

                        # Align metadata with results
                        embeddings = []
                        metadata = []
                        for i, res in enumerate(results):
                            if i < len(valid_rows):
                                embeddings.append(res["embedding"])
                                metadata.append({
                                    "app_name": filename,
                                    "document_name": filename,
                                    "page_number": 0,
                                    "sentence_index": res["sentence_index"],
                                    "sentence": res["sentence"],
                                    "category": batch_df.iloc[i].get("category", ""),
                                    "criterion": batch_df.iloc[i].get("criterion", ""),
                                    "description": batch_df.iloc[i].get("description", "")
                                })
                            else:
                                logging.warning(f"Skipping result {i} in batch {batch_start} of {filename}: index out-of-bounds")
                                logging.warning(f"Expected {len(valid_rows)} results, got {len(results)}. Row {valid_rows[i] if i < len(valid_rows) else 'N/A'}: {batch_df.iloc[i].to_dict() if i < len(batch_df) else 'No row data'}")

                        if not embeddings:
                            logging.warning(f"No valid embeddings for batch {batch_start} of {filename}")
                            continue

                        add_to_index(index, embeddings, metadata, metadata_path, index_path)
                        all_metadata.extend(metadata)
                        logging.info(f"Indexed batch {batch_start} of {filename} with {len(metadata)} entries")

                except Exception as e:
                    logging.error(f"Error processing {filename}: {str(e)}")
                    continue

        if all_metadata:
            with open(metadata_path, "wb") as f:
                pickle.dump(all_metadata, f)
            logging.info(f"Saved metadata with {len(all_metadata)} entries")
            return True
        return False
    except Exception as e:
        logging.error(f"Parse requirements failed: {str(e)}")
        return False