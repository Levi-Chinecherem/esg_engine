from unstructured.partition.pdf import partition_pdf
from utils import logging, file_utils
import pdfplumber

"""
File: esg_system/pdf_extractors/unstructured_extract.py
Role: Extracts text from a single PDF page with complex layouts using Unstructured.io.
Key Functionality:
- Reads a specified page from the input PDF.
- Partitions the page into elements.
- Outputs a dictionary with page number and text.
- Logs extraction success or errors.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

def extract_unstructured(pdf_path, page_num):
    """
    Extract text from a single PDF page using Unstructured.io.
    
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
        logger.debug(f"Attempting Unstructured.io extraction for page {page_num} in {pdf_path}")
        
        # Use pdfplumber to validate page number
        with pdfplumber.open(pdf_path) as pdf:
            if page_num < 1 or page_num > len(pdf.pages):
                logger.error(f"Invalid page number {page_num} for {pdf_path} with {len(pdf.pages)} pages")
                raise ValueError(f"Page number {page_num} out of range")
        
        # Extract elements for the specific page
        elements = partition_pdf(filename=pdf_path, strategy="hi_res", include_page_breaks=True)
        page_text = []
        
        for element in elements:
            element_page = getattr(element.metadata, 'page_number', None)
            if element_page == page_num:
                page_text.append(str(element))
        
        text = ' '.join(page_text).strip() if page_text else ""
        page_data = {
            'page': page_num,
            'text': text,
            'tables': []
        }
        logger.debug(f"Unstructured.io extracted page {page_num}: {len(text)} chars")
        return page_data
    
    except Exception as e:
        logger.warning(f"Unstructured.io extraction failed for page {page_num} in {pdf_path}: {str(e)}")
        raise