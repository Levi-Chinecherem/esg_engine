import pdfplumber
from utils import logging, file_utils

"""
File: esg_system/pdf_extractors/pdfplumber_extract.py
Role: Extracts text and tables from a single PDF page using pdfplumber.
Key Functionality:
- Reads a specified page from the input PDF.
- Extracts text and tables for that page.
- Outputs a dictionary with page number, text, and table data.
- Logs extraction success or errors.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

def extract_pdfplumber(pdf_path, page_num):
    """
    Extract text and tables from a single PDF page using pdfplumber.
    
    Args:
        pdf_path (str): Path to the input PDF file.
        page_num (int): Page number to extract (1-based).
    
    Returns:
        dict: Dictionary with page number, text, and tables (if any).
        Example: {'page': 1, 'text': 'Sample text', 'tables': [[...], [...]]}
    
    Raises:
        FileNotFoundError: If PDF file is missing.
        ValueError: If page_num is invalid.
        Exception: For extraction errors.
    """
    try:
        # Validate PDF path
        file_utils.validate_path(pdf_path)
        logger.debug(f"Attempting pdfplumber extraction for page {page_num} in {pdf_path}")
        
        with pdfplumber.open(pdf_path) as pdf:
            # Validate page number
            if page_num < 1 or page_num > len(pdf.pages):
                logger.error(f"Invalid page number {page_num} for {pdf_path} with {len(pdf.pages)} pages")
                raise ValueError(f"Page number {page_num} out of range")
            
            # Extract page
            page = pdf.pages[page_num - 1]
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            
            page_data = {
                'page': page_num,
                'text': text.strip(),
                'tables': tables
            }
            logger.debug(f"pdfplumber extracted page {page_num}: {len(text)} chars, {len(tables)} tables")
            return page_data
    
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed for page {page_num} in {pdf_path}: {str(e)}")
        raise