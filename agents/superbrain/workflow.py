"""
This module executes the end-to-end workflow for the ESG Engine, processing a report against requirements,
extracting data, validating against standards, summarizing, and saving results to data/output/results.json.

file path: esg_engine/agents/superbrain/workflow.py
"""

import os
import json
import time
import logging
import importlib
from config.settings import get_settings
from rag.reports_rag.cleaner import clean_report_index

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "workflow.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def execute_workflow(report_path, requirements_csv, standard_filter=None):
    """
    Executes the ESG Engine workflow: loads report, fetches requirements, extracts data,
    validates against standards, summarizes, and saves results.
    
    Args:
        report_path (str): Path to the report PDF (e.g., btg-pactual.pdf).
        requirements_csv (str): Path to the requirements CSV (e.g., UNCTAD_requirements.csv).
        standard_filter (str, optional): Specific standard to filter (e.g., "ifrs_s1.pdf").
    
    Returns:
        bool: True if workflow succeeds, False otherwise.
    """
    start_time = time.time()
    
    # Validate inputs
    if not (os.path.exists(report_path) and os.path.exists(requirements_csv)):
        logging.error(f"Invalid input: {report_path} or {requirements_csv} not found")
        return False
    
    try:
        # Initialize system
        from .coordinator import initialize_system
        agents = initialize_system(report_path)
        if not agents:
            logging.error("System initialization failed")
            return False
        
        # Dynamically import agent functions
        def import_function(path):
            module_name, func_name = path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            return getattr(module, func_name)
        
        search_requirements = import_function(agents["requirements_rag"]["searcher"])
        concurrent_extract = import_function(agents["extraction"]["concurrent"])
        validate_data = import_function(agents["evaluation"]["validator"])
        generate_summary = import_function(agents["summarization"]["summarizer"])
        
        # Fetch requirements
        requirements = search_requirements("", app_name=os.path.basename(requirements_csv), k=1000)
        if not requirements:
            logging.warning(f"No requirements found in {requirements_csv}")
            return False
        
        # Extract data from report
        criteria = [req["criterion"] for req in requirements]
        extractions = concurrent_extract(report_path, criteria)
        
        # Validate against standards
        validations = []
        for extraction in extractions:
            validation = validate_data(extraction, standard_filter)
            validations.append(validation)
        
        # Generate summaries
        results = []
        for req, ext, val in zip(requirements, extractions, validations):
            summary = generate_summary(ext, val, req)
            results.append({
                "category": req["category"],
                "criterion": req["criterion"],
                "extracted_sentences": ext.get("matches", []),
                "standard_info": val.get("standard_matches", []),
                "summary": summary,
                "document_name": os.path.basename(report_path),
                "processing_time": time.time() - start_time
            })
        
        # Save results
        output_path = os.path.join(settings["data_paths"]["output"], "results.json")
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        logging.info(f"Saved results to {output_path}")
        
        # Clean up temporary index
        clean_report_index()
        
        return True
    
    except Exception as e:
        logging.error(f"Workflow failed: {str(e)}")
        clean_report_index()
        return False