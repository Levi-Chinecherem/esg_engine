import argparse
import os
from datetime import datetime
from utils import logging, file_utils
from config import Config
from run_audit import run_audit

"""
File: esg_system/main.py
Role: CLI entry point for the ESG Compliance Verification System.
Key Functionality:
- Parses CLI arguments for report, standards, requirements, output directory, and company name.
- Validates input paths and orchestrates the audit workflow via run_audit.py.
- Logs user interactions and errors.
- Handles relative paths correctly to avoid double directory issues (e.g., input/input).
"""

# Initialize logger
logger = logging.setup_logger(__name__)

def main():
    """
    Main function to parse CLI arguments and run the ESG audit.

    Args:
        None (parses sys.argv)

    Returns:
        None

    Raises:
        FileNotFoundError: If input files or directories are invalid.
        Exception: For other processing errors.
    """
    try:
        parser = argparse.ArgumentParser(description="ESG Compliance Verification System")
        parser.add_argument("--report", required=True, help="Path to company report PDF (e.g., input/btg-pactual.pdf)")
        parser.add_argument("--standards", required=True, help="Path to standards PDF (e.g., standards/ifrs_s1.pdf)")
        parser.add_argument("--requirements", required=True, help="Path to requirements CSV (e.g., requirements/UNCTAD_requirements.csv)")
        parser.add_argument("--output", required=True, help="Output directory (e.g., output)")
        parser.add_argument("--company", default="Company", help="Company name for the report (e.g., BTG Pactual)")
        args = parser.parse_args()

        # Initialize configuration
        config = Config(standards_file=os.path.basename(args.standards),
                        requirements_file=os.path.basename(args.requirements))
        
        # Normalize and validate paths
        input_dir = config.input_dir
        report_path = os.path.normpath(args.report).replace('input' + os.sep, '')  # Strip leading 'input/'
        report_path = os.path.join(input_dir, report_path)
        standards_path = os.path.join(config.standards_dir, os.path.basename(args.standards))
        requirements_path = os.path.join(config.requirements_dir, os.path.basename(args.requirements))
        output_dir = os.path.join(config.project_root, args.output)

        # Validate paths
        file_utils.validate_path(report_path)
        file_utils.validate_path(standards_path)
        file_utils.validate_path(requirements_path)
        file_utils.validate_path(output_dir)

        # Run audit workflow
        logger.info(f"Starting CLI execution: report={report_path}, standards={standards_path}, requirements={requirements_path}")
        csv_path = run_audit(report_path, standards_path, requirements_path, output_dir, args.company)
        logger.info(f"Audit completed. CSV report saved to: {csv_path}")

    except Exception as e:
        logger.error(f"CLI execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()