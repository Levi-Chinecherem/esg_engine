import fitz  # PyMuPDF
from utils import logging, file_utils

"""
File: esg_system/pdf_extractors/pymupdf_extract.py
Role: Extracts text from a single PDF page using PyMuPDF for high-speed processing.
Key Functionality:
- Reads a specified page from the input PDF.
- Extracts text for that page.
- Outputs a dictionary with page number and text.
- Logs extraction success or errors.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

def extract_pymupdf(pdf_path, page_num):
    """
    Extract text from a single PDF page using PyMuPDF.
    
    Args:
        pdf_path (str): Path to the input PDF file.
        page_num (int): Page number to extract (1-based).
    
    Returns:
        dict: Dictionary with page number and text.
        Example: {'page': 1, 'text': 'Sample text', 'tables': []}
    
    Raises:
        FileNotFoundError: If PDF file is missing.
        ValueError: If page_num is invalid.
        Exception: For extraction errors.
    """
    try:
        # Validate PDF path
        file_utils.validate_path(pdf_path)
        logger.debug(f"Attempting PyMuPDF extraction for page {page_num} in {pdf_path}")
        
        with fitz.open(pdf_path) as pdf:
            # Validate page number
            if page_num < 1 or page_num > pdf.page_count:
                logger.error(f"Invalid page number {page_num} for {pdf_path} with {pdf.page_count} pages")
                raise ValueError(f"Page number {page_num} out of range")
            
            # Extract page
            page = pdf[page_num - 1]
            text = page.get_text("text") or ""
            
            page_data = {
                'page': page_num,
                'text': text.strip(),
                'tables': []
            }
            logger.debug(f"PyMuPDF extracted page {page_num}: {len(text)} chars")
            return page_data
    
    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed for page {page_num} in {pdf_path}: {str(e)}")
        raise