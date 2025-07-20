import time
from datetime import datetime
from utils import logging, file_utils, pdf_extraction
from build_database import DatabaseBuilder
from pdf_extractors.text_organizer import organize_text
from data_extraction.mistral_extract import extract_data
from compliance_check.compliance_validator import validate_compliance
from report_generator.csv_generator import generate_csv_report
from config import Config
import os
import spacy

"""
File: run_audit.py
Role: Orchestrates the ESG audit workflow for the ESG Compliance Verification System.
Key Functionality:
- Initializes a single SpaCy en_core_web_sm model instance for reuse in DatabaseBuilder, TextOrganizer, and ComplianceValidator.
- Extracts and organizes PDF text into ESG categories at the paragraph level.
- Validates compliance against standards with dynamic thresholds and paragraph embeddings.
- Generates CSV report with Source_Granularity and detailed Compliance_Reason.
- Logs workflow progress, model IDs, category distribution, table counts, and errors.
"""

logger = logging.setup_logger(__name__)

def run_audit(report_path, standards_path, requirements_path, output_dir, company_name):
    """
    Run the ESG audit workflow and generate a CSV report.
    
    Args:
        report_path (str): Path to the input report PDF (e.g., btg-pactual.pdf).
        standards_path (str): Path to the standards PDF (e.g., ifrs_s1.pdf).
        requirements_path (str): Path to the requirements CSV (e.g., UNCTAD_requirements.csv).
        output_dir (str): Directory for output CSV report.
        company_name (str): Name of the company being audited.
    
    Returns:
        str: Path to the generated CSV report.
    
    Raises:
        FileNotFoundError: If input files are missing.
        ValueError: If inputs are invalid.
        Exception: For other workflow failures.
    """
    try:
        start_time = time.time()
        logger.info(f"Starting ESG audit workflow: report={report_path}, standards={standards_path}, requirements={requirements_path}, output_dir={output_dir}, company={company_name}")
        
        # Validate input paths
        for path in [report_path, standards_path, requirements_path]:
            file_utils.validate_path(path)
        
        # Initialize SpaCy model for embeddings
        config = Config()
        embedding_model = spacy.load('en_core_web_sm')
        logger.info(f"Initialized SpaCy en_core_web_sm model, id={id(embedding_model)}")
        
        # Initialize database
        logger.info("Starting database initialization")
        db_builder = DatabaseBuilder([standards_path], requirements_path)
        logger.info(f"DatabaseBuilder embedding model id={id(db_builder.embedding_model)}")
        collections, requirements_df = db_builder.initialize_database()
        logger.info(f"Database initialized with {len(collections)} standards collections and {len(requirements_df)} criteria")
        
        # Extract PDF text and tables
        logger.info("Starting PDF extraction")
        extracted_data = pdf_extraction.extract_pdf_with_fallback(report_path)
        table_count = sum(len(page.get('tables', [])) for page in extracted_data)
        logger.info(f"Extracted {len(extracted_data)} pages with {table_count} tables from {report_path}")
        
        # Organize text into categories
        logger.info("Starting text organization")
        categorized_data = organize_text(extracted_data, requirements_path, embedding_model=embedding_model)
        category_counts = {cat: len(categorized_data.get(cat, [])) for cat in categorized_data}
        logger.info(f"Categorized data: {category_counts}")
        
        # Extract data
        logger.info("Starting data extraction")
        criteria_data = extract_data(categorized_data, requirements_path)
        logger.info(f"Extracted data for {len(criteria_data)} criteria")
        
        # Validate compliance
        logger.info("Starting compliance validation")
        compliance_results, summary = validate_compliance(criteria_data, requirements_path, categorized_data, embedding_model=embedding_model)
        compliant_count = sum(1 for result in compliance_results if result['status'] == 'Compliant')
        logger.info(f"Validated compliance for {len(compliance_results)} criteria, {compliant_count} compliant")
        
        # Generate CSV report
        logger.info("Starting CSV report generation")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_time = round(time.time() - start_time, 1)
        output_path = generate_csv_report(
            compliance_results,  # Pass compliance_results separately
            summary,            # Pass summary separately
            requirements_path,
            os.path.basename(report_path),
            timestamp,
            total_time,
            output_dir
        )
        logger.info(f"CSV report generated: {output_path}, total time: {total_time} seconds")
        
        logger.info(f"ESG audit completed in {total_time} seconds")
        return output_path
    
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Invalid input: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Audit workflow failed: {str(e)}")
        raise