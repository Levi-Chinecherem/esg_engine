import os
import pandas as pd
from utils import logging, file_utils
from datetime import datetime

"""
File: esg_system/report_generator/csv_generator.py
Role: Generates a CSV report summarizing ESG compliance results with enhanced output.
Key Functionality:
- Creates a summary section with metrics (Total_Criteria_Assessed, Compliant_Criteria, NonCompliant_Criteria, Compliance_Rate, Processing_Time_Seconds).
- Creates a detailed section with per-criterion data, including Source_Granularity and detailed Compliance_Reason.
- Saves the report as <filename>_result.csv (e.g., btg-pactual_result.csv).
- Logs generation steps and errors for traceability.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

def generate_csv_report(compliance_results, summary, requirements_path, document_name, audit_date, processing_time, output_dir):
    """
    Generate a CSV report with summary and detailed ESG compliance results.
    
    Args:
        compliance_results (list): List of dictionaries with criterion-specific compliance data.
        summary (list): List of dictionaries with summary statistics.
        requirements_path (str): Path to the requirements CSV.
        document_name (str): Name of the processed document (e.g., btg-pactual.pdf).
        audit_date (str): Audit date in YYYY-MM-DD HH:MM:SS format.
        processing_time (float): Total processing time in seconds.
        output_dir (str): Directory to save the CSV report.
    
    Returns:
        str: Path to the generated CSV file.
    
    Raises:
        ValueError: If compliance_results or requirements CSV is invalid.
        OSError: If file writing fails.
    """
    try:
        # Validate inputs
        if not compliance_results:
            logger.error("No compliance results provided for CSV generation")
            raise ValueError("Compliance results list is empty")
        
        file_utils.validate_path(requirements_path)
        requirements_df = pd.read_csv(requirements_path)
        if not all(col in requirements_df.columns for col in ['category', 'criterion', 'description']):
            logger.error("Requirements CSV missing required columns: category, criterion, description")
            raise ValueError("Requirements CSV missing required columns")
        
        logger.info(f"Starting CSV report generation for {document_name}")
        
        # Verify summary data
        if not summary:
            logger.warning("No summary data provided; generating default summary")
            total_criteria = len(compliance_results)
            compliant_count = sum(1 for result in compliance_results if result.get('status') == 'Compliant')
            non_compliant_count = total_criteria - compliant_count
            compliance_rate = (compliant_count / total_criteria * 100) if total_criteria > 0 else 0
            summary = [
                {'SUMMARY_HEADER': 'Total_Criteria_Assessed', 'SUMMARY_VALUE': total_criteria},
                {'SUMMARY_HEADER': 'Compliant_Criteria', 'SUMMARY_VALUE': compliant_count},
                {'SUMMARY_HEADER': 'NonCompliant_Criteria', 'SUMMARY_VALUE': non_compliant_count},
                {'SUMMARY_HEADER': 'Compliance_Rate', 'SUMMARY_VALUE': f"{compliance_rate:.1f}%"},
                {'SUMMARY_HEADER': 'Processing_Time_Seconds', 'SUMMARY_VALUE': f"{processing_time:.1f}"}
            ]
        
        # Prepare detailed data
        detailed_data = []
        for result in compliance_results:
            criterion = result.get('criterion', '')
            req_row = requirements_df[requirements_df['criterion'] == criterion]
            if req_row.empty:
                logger.warning(f"No requirements data found for criterion: {criterion}")
                continue
            
            category = req_row['category'].iloc[0]
            description = req_row['description'].iloc[0]
            
            # Generate human-readable summary
            human_summary = f"{document_name.rsplit('.', 1)[0]} {'reported' if result.get('value') else 'mentioned'} {criterion.replace('_', ' ')} on page {result.get('page', 'N/A')}, {'meeting' if result.get('status') == 'Compliant' else 'not meeting'} the disclosure requirement of {result.get('framework', '')} {result.get('code', '')}."
            
            detailed_data.append({
                'Document_Processed': document_name,
                'Audit_Date': audit_date,
                'Category': category,
                'Criterion': criterion,
                'Description': description,
                'Extracted_Value': result.get('value', ''),
                'Unit': result.get('unit', ''),
                'Source_Page': result.get('page', ''),
                'Source_Granularity': result.get('source_granularity', ''),
                'Standard_Framework': result.get('framework', ''),
                'Standard_Code': result.get('code', ''),
                'Standard_Requirement': description,
                'Compliance_Status': result.get('status', ''),
                'Compliance_Reason': result.get('reason', ''),
                'Human_Summary': human_summary
            })
        
        # Combine summary and detailed data with a blank row separator
        final_data = summary + [{}] + detailed_data
        df = pd.DataFrame(final_data, columns=[
            'SUMMARY_HEADER', 'SUMMARY_VALUE', 'Document_Processed', 'Audit_Date', 'Category',
            'Criterion', 'Description', 'Extracted_Value', 'Unit', 'Source_Page',
            'Source_Granularity', 'Standard_Framework', 'Standard_Code', 'Standard_Requirement',
            'Compliance_Status', 'Compliance_Reason', 'Human_Summary'
        ])
        
        # Save to CSV
        base_filename = document_name.rsplit('.', 1)[0]
        output_filename = f"{base_filename}_result.csv"
        output_path = os.path.join(output_dir, output_filename)
        file_utils.validate_path(output_dir)
        df.to_csv(output_path, index=False)
        logger.info(f"Generated CSV report: {output_path} with {len(summary)} summary rows and {len(detailed_data)} detailed rows")
        
        return output_path
    
    except Exception as e:
        logger.error(f"CSV report generation failed: {str(e)}")
        raise