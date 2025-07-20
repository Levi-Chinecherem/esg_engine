"""
Main entry point for the ESG Engine. Orchestrates indexing of standards and reports,
parsing of requirements, and executes the full workflow to produce results.json.

file path: esg_engine/main.py
"""

import argparse
import logging
import os
from config.settings import get_settings
from rag.standards_rag.indexer import index_standards
from rag.reports_rag.indexer import index_report
from rag.requirements_rag.parser import parse_requirements
from utils.resource_monitor import check_resources
from agents.superbrain.workflow import execute_workflow

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "workflow.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_workflow(report_path, requirements_path):
    """
    Runs the ESG Engine workflow: indexes standards and report, parses requirements,
    and executes the full workflow to produce results.json.

    Args:
        report_path (str): Path to the report PDF.
        requirements_path (str): Path to the requirements CSV.

    Returns:
        bool: True if workflow completes successfully, False otherwise.
    """
    try:
        if not check_resources()["compliant"]:
            logging.error("Resource usage exceeds limit, aborting workflow")
            return False

        # Index standards and requirements once
        logging.info("Starting standards indexing")
        if not index_standards():
            logging.warning("Standards indexing failed, continuing with available indexes")
        logging.info("Starting requirements parsing")
        if not parse_requirements():
            logging.error(f"Failed to parse requirements: {requirements_path}")
            return False

        logging.info(f"Indexing report: {report_path}")
        if not index_report(report_path):
            logging.error(f"Failed to index report: {report_path}")
            return False

        logging.info("Starting full ESG Engine workflow")
        success = execute_workflow(report_path, requirements_path)
        if not success:
            logging.error("Full workflow execution failed")
            return False

        output_path = os.path.join(settings["data_paths"]["output"], "results.json")
        print(f"Workflow completed successfully. Results saved to {output_path}")
        return True

    except Exception as e:
        logging.error(f"Workflow failed: {str(e)}")
        print(f"Error: Workflow failed: {str(e)}")
        return False

def main():
    """
    Parses command-line arguments and runs the ESG Engine workflow.
    """
    parser = argparse.ArgumentParser(description="ESG Engine Workflow")
    parser.add_argument("--report", required=True, help="Path to the report PDF")
    parser.add_argument("--requirements", required=True, help="Path to the requirements CSV")
    args = parser.parse_args()

    logging.info(f"Starting workflow with report: {args.report}, requirements: {args.requirements}")
    success = run_workflow(args.report, args.requirements)
    if not success:
        logging.error("Workflow execution failed")
        print("Error: Workflow failed")
        exit(1)

if __name__ == "__main__":
    main()