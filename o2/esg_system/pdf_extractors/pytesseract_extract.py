import pytesseract
from pdf2image import convert_from_path
from utils import logging, file_utils
from config import Config
import pdfplumber

"""
File: esg_system/pdf_extractors/pytesseract_extract.py
Role: Performs OCR on a single PDF page using pytesseract.
Key Functionality:
- Converts a specified PDF page to an image using pdf2image.
- Extracts text from the image using pytesseract.
- Outputs a dictionary with page number and text.
- Logs extraction success or errors.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

def extract_pytesseract(pdf_path, page_num):
    """
    Extract text from a single PDF page using pytesseract.
    
    Args:
        pdf_path (str): Path to the input PDF file.
        page_num (int): Page number to extract (1-based).
    
    Returns:
        dict: Dictionary with page number and text.
        Example: {'page': 1, 'text': 'Sample text', 'tables': []}
    
    Raises:
        FileNotFoundError: If PDF file or Tesseract executable is missing.
        ValueError: If page_num is invalid.
        Exception: For OCR extraction errors.
    """
    try:
        # Validate PDF path and Tesseract executable
        file_utils.validate_path(pdf_path)
        config = Config()
        pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd
        file_utils.validate_path(config.tesseract_cmd)
        logger.debug(f"Attempting pytesseract extraction for page {page_num} in {pdf_path}")
        
        # Use pdfplumber to validate page number
        with pdfplumber.open(pdf_path) as pdf:
            if page_num < 1 or page_num > len(pdf.pages):
                logger.error(f"Invalid page number {page_num} for {pdf_path} with {len(pdf.pages)} pages")
                raise ValueError(f"Page number {page_num} out of range")
        
        # Convert specific page to image
        images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
        if not images:
            logger.warning(f"No image generated for page {page_num} in {pdf_path}")
            raise Exception("Failed to convert page to image")
        
        # Perform OCR
        text = pytesseract.image_to_string(images[0], lang='eng') or ""
        page_data = {
            'page': page_num,
            'text': text.strip(),
            'tables': []
        }
        logger.debug(f"pytesseract extracted page {page_num}: {len(text)} chars")
        return page_data
    
    except Exception as e:
        logger.warning(f"pytesseract extraction failed for page {page_num} in {pdf_path}: {str(e)}")
        raise