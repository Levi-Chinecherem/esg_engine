"""
This module serves as the main entry point for the ESG Engine, providing a command-line interface
to process ESG reports against requirements and standards, coordinating agents and saving results
to data/output/results.json.

file path: esg_engine/main.py
"""

import argparse
import os
import logging
import time
from config.settings import get_settings
from agents.superbrain.coordinator import initialize_system
from agents.superbrain.workflow import execute_workflow
from utils.resource_monitor import check_resources

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "main.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    """
    Main entry point for the ESG Engine, parsing CLI arguments, initializing the system,
    executing the workflow, and saving results.
    
    Args:
        None (uses command-line arguments)
    
    Returns:
        None
    """
    # Set up CLI parser
    parser = argparse.ArgumentParser(description="ESG Engine: Process ESG reports against requirements and standards.")
    parser.add_argument("--report", required=True, help="Path to the ESG report PDF (e.g., btg-pactual.pdf)")
    parser.add_argument("--requirements", required=True, help="Path to the requirements CSV (e.g., UNCTAD_requirements.csv)")
    parser.add_argument("--standard", help="Optional standard to filter (e.g., ifrs_s1.pdf)")
    args = parser.parse_args()
    
    # Validate inputs
    if not (os.path.exists(args.report) and os.path.exists(args.requirements)):
        logging.error(f"Invalid input: {args.report} or {args.requirements} not found")
        print(f"Error: {args.report} or {args.requirements} not found")
        return
    
    # Check resource limits
    if not check_resources():
        logging.error("Resource usage exceeds 45% limit, aborting")
        print("Error: Resource usage exceeds 45% limit")
        return
    
    # Initialize system
    start_time = time.time()
    agents = initialize_system(args.report)
    if not agents:
        logging.error("System initialization failed")
        print("Error: System initialization failed")
        return
    
    # Execute workflow
    try:
        success = execute_workflow(args.report, args.requirements, args.standard)
        processing_time = time.time() - start_time
        
        if success:
            logging.info(f"Workflow completed successfully in {processing_time:.2f} seconds")
            print(f"Workflow completed successfully in {processing_time:.2f} seconds")
            print(f"Results saved to {os.path.join(settings['data_paths']['output'], 'results.json')}")
        else:
            logging.error("Workflow failed")
            print("Error: Workflow failed")
    
    except Exception as e:
        logging.error(f"Workflow execution failed: {str(e)}")
        print(f"Error: Workflow execution failed: {str(e)}")

if __name__ == "__main__":
    main()