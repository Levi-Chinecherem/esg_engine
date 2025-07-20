import pandas as pd
import jinja2
import os
import subprocess
from utils import logging, file_utils
from config import Config

"""
File: esg_system/report_generator/pdf_generator.py
Role: Generates a PDF report from compliance results and supplementary data using a LaTeX template.
Key Functionality:
- Loads the LaTeX template (esg_compliance_report_template.tex) and populates it with CSV data and supplementary data.
- Maps compliance data (CSV) and supplementary data (company profile, case studies, charts) to template placeholders.
- Compiles the report to PDF using latexmk, saving to the output directory.
- Logs compilation steps and errors for traceability.
- Ensures compilation completes in ~12 seconds.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

def generate_pdf_report(csv_path, template_path, output_dir, company_name="Company", supplementary_data=None):
    """
    Generate a PDF report from the CSV compliance results and supplementary data using a LaTeX template.
    
    Args:
        csv_path (str): Path to the input CSV file (e.g., Acme_Corp_2023_result.csv).
        template_path (str): Path to the LaTeX template (e.g., esg_compliance_report_template.tex).
        output_dir (str): Directory to save the PDF report.
        company_name (str, optional): Company name for the report. Defaults to 'Company'.
        supplementary_data (dict, optional): Supplementary data from supplementary_extract.py.
    
    Returns:
        str: Path to the generated PDF file.
    
    Raises:
        FileNotFoundError: If CSV or template file is missing.
        ValueError: If CSV is invalid or empty.
        subprocess.CalledProcessError: If LaTeX compilation fails.
    """
    try:
        # Validate inputs
        file_utils.validate_path(csv_path)
        file_utils.validate_path(template_path)
        file_utils.validate_path(output_dir)
        if supplementary_data is None:
            supplementary_data = {}
        
        logger.info(f"Starting PDF report generation from {csv_path}")
        
        # Load CSV data
        df = pd.read_csv(csv_path)
        if df.empty:
            logger.error("CSV file is empty")
            raise ValueError("CSV file is empty")
        
        # Extract summary statistics
        summary_df = df[df['SUMMARY_HEADER'].notnull()]
        summary = {
            'total_criteria': int(summary_df[summary_df['SUMMARY_HEADER'] == 'Total_Criteria_Assessed']['SUMMARY_VALUE'].iloc[0]),
            'compliant_criteria': int(summary_df[summary_df['SUMMARY_HEADER'] == 'Compliant_Criteria']['SUMMARY_VALUE'].iloc[0]),
            'non_compliant_criteria': int(summary_df[summary_df['SUMMARY_HEADER'] == 'NonCompliant_Criteria']['SUMMARY_VALUE'].iloc[0]),
            'compliance_rate': float(summary_df[summary_df['SUMMARY_HEADER'] == 'Compliance_Rate']['SUMMARY_VALUE'].iloc[0].rstrip('%')),
            'processing_time': float(summary_df[summary_df['SUMMARY_HEADER'] == 'Processing_Time_Seconds']['SUMMARY_VALUE'].iloc[0])
        }
        
        # Extract detailed data by category
        detailed_df = df[df['Criterion'].notnull()]
        environmental_data = detailed_df[detailed_df['Category'] == 'Environmental'][['Criterion', 'Description', 'Extracted_Value', 'Unit', 'Source_Page', 'Standard_Code', 'Compliance_Status', 'Compliance_Reason']].to_dict('records')
        social_data = detailed_df[detailed_df['Category'] == 'Social'][['Criterion', 'Description', 'Extracted_Value', 'Unit', 'Source_Page', 'Standard_Code', 'Compliance_Status', 'Compliance_Reason']].to_dict('records')
        governance_data = detailed_df[detailed_df['Category'] == 'Governance'][['Criterion', 'Description', 'Extracted_Value', 'Unit', 'Source_Page', 'Standard_Code', 'Compliance_Status', 'Compliance_Reason']].to_dict('records')
        
        # Prepare recommendations dynamically based on non-compliant criteria
        recommendations = []
        non_compliant = detailed_df[detailed_df['Compliance_Status'] == 'Non-Compliant']
        if not non_compliant.empty:
            recommendations.append({
                'title': 'Improve Disclosure Methodology',
                'description': 'Provide detailed methodologies for non-compliant metrics to meet standards.',
                'rationale': f"Non-compliance in {', '.join(non_compliant['Criterion'].tolist())} due to missing methodologies."
            })
        if any('Scope3' in criterion for criterion in detailed_df['Criterion']):
            recommendations.append({
                'title': 'Enhance Scope 3 Reporting',
                'description': 'Include supply chain emissions data to align with GRI 305-3.',
                'rationale': 'Partial disclosure limits full compliance.'
            })
        if not recommendations:
            recommendations = [{'title': 'Maintain Compliance', 'description': 'Continue robust reporting practices.', 'rationale': 'All criteria compliant.'}]
        
        # Prepare data for LaTeX template
        template_data = {
            'company_name': company_name,
            'audit_date': detailed_df['Audit_Date'].iloc[0] if not detailed_df.empty else '2025-07-19 12:24:00',
            'total_criteria': summary['total_criteria'],
            'compliant_criteria': summary['compliant_criteria'],
            'non_compliant_criteria': summary['non_compliant_criteria'],
            'compliance_rate': summary['compliance_rate'],
            'processing_time': summary['processing_time'],
            'environmental_data': environmental_data,
            'social_data': social_data,
            'governance_data': governance_data,
            'environmental_count': len(environmental_data),
            'social_count': len(social_data),
            'governance_count': len(governance_data),
            'environmental_compliant': sum(1 for item in environmental_data if item['Compliance_Status'] == 'Compliant'),
            'social_compliant': sum(1 for item in social_data if item['Compliance_Status'] == 'Compliant'),
            'governance_compliant': sum(1 for item in governance_data if item['Compliance_Status'] == 'Compliant'),
            'company_profile': supplementary_data.get('company_profile', {'about': 'N/A', 'mission': 'N/A', 'vision': 'N/A', 'core_values': []}),
            'stakeholder_engagement': supplementary_data.get('stakeholder_engagement', {'survey_satisfaction': 'N/A', 'forums': 'N/A', 'meetings': 'N/A', 'themes': []}),
            'case_studies': supplementary_data.get('case_studies', []),
            'emissions_data': supplementary_data.get('emissions_data', []),
            'diversity_data': supplementary_data.get('diversity_data', []),
            'benchmarking_data': supplementary_data.get('benchmarking_data', []),
            'progress_data': supplementary_data.get('progress_data', []),
            'recommendations': recommendations
        }
        
        # Load LaTeX template
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(template_path)))
        template = env.get_template(os.path.basename(template_path))
        rendered_tex = template.render(**template_data)
        
        # Save rendered LaTeX to temporary file
        temp_tex_path = os.path.join(output_dir, 'temp_report.tex')
        with open(temp_tex_path, 'w', encoding='utf-8') as f:
            f.write(rendered_tex)
        logger.debug(f"Rendered LaTeX saved to {temp_tex_path}")
        
        # Compile LaTeX to PDF
        output_pdf = os.path.join(output_dir, 'audit_report.pdf')
        try:
            subprocess.run(
                ['latexmk', '-pdf', '-quiet', temp_tex_path, '-outdir=' + output_dir],
                check=True, capture_output=True, text=True
            )
            logger.info(f"Generated PDF report: {output_pdf}")
        finally:
            # Clean up temporary files
            for ext in ['.aux', '.log', '.fls', '.fdb_latexmk', '.tex']:
                temp_file = os.path.join(output_dir, f'temp_report{ext}')
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
        
        return output_pdf
    
    except Exception as e:
        logger.error(f"PDF report generation failed: {str(e)}")
        raise