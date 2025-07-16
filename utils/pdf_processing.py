"""
This module provides functionality to extract text from PDF files page by page for the ESG Engine.
It uses pdfplumber to process PDFs and handles errors by logging to a file.

file path: esg_engine/utils/pdf_processing.py
"""

import pdfplumber
import logging
import os
from config.settings import get_settings

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "errors.log")
logging.basicConfig(filename=log_file, level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_pdf_text(pdf_path):
    """
    Extracts text from a PDF file page by page, returning a list of dictionaries with page numbers and text.
    
    Args:
        pdf_path (str): Path to the PDF file.
    
    Returns:
        list: List of dictionaries with keys 'page_number' (int) and 'text' (str).
    
    Raises:
        FileNotFoundError: If the PDF file does not exist.
        Exception: For other PDF processing errors, logged to errors.log.
    """
    # Initialize result list
    pages = []
    
    try:
        # Check if file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Open PDF with pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            # Iterate through each page
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                # Skip empty pages
                if text.strip():
                    pages.append({"page_number": page_num, "text": text})
                # Log empty pages for debugging
                else:
                    logging.warning(f"Empty page {page_num} in {pdf_path}")
                    
        return pages
    
    except FileNotFoundError as e:
        # Log file not found error
        logging.error(str(e))
        raise
    except Exception as e:
        # Log other PDF processing errors
        logging.error(f"Error processing PDF {pdf_path}: {str(e)}")
        return []