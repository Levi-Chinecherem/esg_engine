"""
This module executes the end-to-end workflow for the ESG Engine, processing a report against requirements,
extracting data, validating against standards, summarizing, and saving results to data/output/results.json.
It reuses precomputed standards and requirements caches from their respective directories to avoid redundant processing.

file path: esg_engine/agents/superbrain/workflow.py
"""

import pandas as pd
import os
import logging
import pickle
import time
from config.settings import get_settings
from agents.extraction.searcher import extract_data
from agents.evaluation.validator import validate_data
import json
from sentence_transformers import SentenceTransformer
import torch

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "workflow.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Cache configuration
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".esg_engine_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Load model for embedding requirements
model = SentenceTransformer('all-MiniLM-L6-v2')

def load_requirements(requirements_path: str) -> list:
    """
    Loads requirements from a CSV file and precomputes embeddings.

    Args:
        requirements_path (str): Path to the requirements CSV file.

    Returns:
        list: List of dictionaries with category, criterion, description, and embedding.
    """
    try:
        df = pd.read_csv(requirements_path)
        requirements = []
        for _, row in df.iterrows():
            criterion = row["criterion"]
            embedding = model.encode(criterion.lower(), convert_to_tensor=True)
            requirements.append({
                "category": row["category"],
                "criterion": criterion,
                "description": row.get("description", ""),
                "embedding": embedding
            })
        logging.info(f"Loaded {len(requirements)} requirements from {requirements_path}")
        return requirements
    except Exception as e:
        logging.error(f"Failed to load requirements from {requirements_path}: {str(e)}")
        return []

def load_cached_texts(reports_dir: str, standards_dir: str) -> tuple:
    """
    Loads cached report and standard texts.

    Args:
        reports_dir (str): Directory for report texts.
        standards_dir (str): Directory for standard texts.

    Returns:
        tuple: (report_texts, standards_texts, standards_cache, requirements_cache)
    """
    report_texts = {}
    standards_texts = {}
    standards_cache = []
    requirements_cache = []

    reports_text_cache_path = os.path.join(reports_dir, "texts_cache.pkl")
    if os.path.exists(reports_text_cache_path):
        with open(reports_text_cache_path, "rb") as f:
            cached_texts = pickle.load(f)
            report_texts = cached_texts.get("reports", {})
        logging.info(f"Loaded report texts from {reports_text_cache_path}")

    standards_text_cache_path = os.path.join(standards_dir, "texts_cache.pkl")
    if os.path.exists(standards_text_cache_path):
        with open(standards_text_cache_path, "rb") as f:
            cached_texts = pickle.load(f)
            standards_texts = cached_texts.get("standards", {})
        logging.info(f"Loaded standards texts from {standards_text_cache_path}")

    standards_cache_path = os.path.join(standards_dir, "standards_cache.pkl")
    if os.path.exists(standards_cache_path):
        with open(standards_cache_path, "rb") as f:
            standards_cache = pickle.load(f)
        logging.info(f"Loaded standards cache from {standards_cache_path}")

    return report_texts, standards_texts, standards_cache, requirements_cache

def generate_summary(criterion: str, extracted_sentences: list, standard_matches: list) -> str:
    """
    Generates a summary for the criterion based on extracted sentences and standard matches.

    Args:
        criterion (str): The criterion being evaluated.
        extracted_sentences (list): List of extracted report sentences.
        standard_matches (list): List of standard matches.

    Returns:
        str: Summary text.
    """
    if extracted_sentences and standard_matches:
        return f"Summary for {criterion}: Compliant with standards, found {len(extracted_sentences)} report matches and {len(standard_matches)} standard matches."
    elif extracted_sentences:
        return f"Summary for {criterion}: Found {len(extracted_sentences)} report matches but no standard matches."
    elif standard_matches:
        return f"Summary for {criterion}: Found {len(standard_matches)} standard matches but no report matches."
    else:
        return f"Summary for {criterion}: No matches found."

def execute_workflow(report_path: str, requirements_path: str, standard_filter: str = None) -> None:
    """
    Orchestrates the ESG Engine workflow, extracting data from reports, validating against standards,
    and producing results.json.

    Args:
        report_path (str): Path to the report PDF.
        requirements_path (str): Path to the requirements CSV.
        standard_filter (str, optional): Specific standard to filter (e.g., "ifrs_s1.pdf").
    """
    start_time = time.time()
    results = []

    # Load requirements and cached texts
    requirements = load_requirements(requirements_path)
    reports_dir = settings["data_paths"]["reports"]
    standards_dir = settings["data_paths"]["standards"]
    report_texts, standards_texts, standards_cache, requirements_cache = load_cached_texts(reports_dir, standards_dir)

    # Process each requirement
    for req in requirements:
        criterion = req["criterion"]
        description = req["description"]
        category = req["category"]
        logging.info(f"Processing criterion: {criterion}")

        # Step 1: Extract report data
        report_key = os.path.basename(report_path)
        page_texts = report_texts.get(report_key, {})
        extraction = extract_data(report_path, criterion, description, page_texts)
        extracted_matches = extraction.get("matches", [])

        # Step 2: Validate against standards
        validation = validate_data(
            extraction=extraction,
            standard_filter=standard_filter,
            standards_texts=standards_texts,
            standards_cache=standards_cache,
            requirements_cache=[req]  # Pass single requirement for efficiency
        )

        # Step 3: Generate summary
        summary = generate_summary(criterion, validation["extracted_sentences"], validation["standard_matches"])

        # Step 4: Compile result
        result = {
            "category": category,
            "criterion": criterion,
            "extracted_sentences": validation["extracted_sentences"],
            "standard_info": validation["standard_matches"],
            "summary": summary,
            "document_name": report_key,
            "processing_time": time.time() - start_time,
            "compliance": validation["compliance"]
        }
        results.append(result)
        logging.info(f"Completed processing for '{criterion}': Compliance={validation['compliance']}, Extracted={len(validation['extracted_sentences'])}, Standards={len(validation['standard_matches'])}")

    # Write results to JSON
    output_dir = settings["data_paths"]["output"]
    output_path = os.path.join(output_dir, "results.json")
    os.makedirs(output_dir, exist_ok=True)
    try:
        with open(output_path, "w") as f:
            json.dump(results, f, indent=4)
        logging.info(f"Results written to {output_path}")
    except Exception as e:
        logging.error(f"Failed to write results to {output_path}: {str(e)}")

    total_time = time.time() - start_time
    logging.info(f"Workflow completed in {total_time:.2f} seconds")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ESG Engine Workflow")
    parser.add_argument("--report", required=True, help="Path to the report PDF")
    parser.add_argument("--requirements", required=True, help="Path to the requirements CSV")
    parser.add_argument("--standard", help="Specific standard to filter (e.g., ifrs_s1.pdf)")
    args = parser.parse_args()
    execute_workflow(args.report, args.requirements, args.standard)