import pdfplumber
import pandas as pd
import re
from utils import logging, file_utils
from pdf_extractors import pdfplumber_extract, pymupdf_extract, unstructured_extract, pytesseract_extract

"""
File: esg_system/utils/pdf_extraction.py
Role: Provides a page-by-page fallback mechanism for PDF extraction with enhanced table parsing.
Key Functionality:
- Extracts text and tables using pdfplumber as the primary method.
- Falls back to PyMuPDF, Unstructured.io, and pytesseract for text if pdfplumber fails.
- Extracts tables with pdfplumber using refined settings for better accuracy.
- Structures tables as headers or key-value pairs for compatibility with text_organizer.py.
- Skips pages where all extractors fail, logging the failure.
- Logs extraction attempts, successes, and errors for traceability.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

def extract_pdf_with_fallback(pdf_path):
    """
    Extract text and tables from a PDF using a page-by-page fallback mechanism.
    
    Args:
        pdf_path (str): Path to the input PDF file.
    
    Returns:
        list: List of dictionaries with page number, text, and structured tables.
        Example: [{'page': 1, 'text': 'Sample text', 'tables': [{'header': ['Revenue', 'Amount'], 'data': [['Revenue', '1200000000 USD']]}], 'source': 'pdfplumber'}, ...]
    
    Raises:
        FileNotFoundError: If PDF file is missing.
        Exception: If page counting fails.
    """
    try:
        file_utils.validate_path(pdf_path)
        logger.info(f"Starting page-by-page PDF extraction with fallback for {pdf_path}")
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
        logger.info(f"Detected {total_pages} pages in {pdf_path}")
        
        extracted_data = []
        
        for page_num in range(1, total_pages + 1):
            logger.info(f"Processing page {page_num}")
            page_data = None
            
            try:
                page_data = pdfplumber_extract.extract_pdfplumber(pdf_path, page_num)
                if page_data['text'].strip():
                    page_data['source'] = 'pdfplumber'
                    logger.info(f"pdfplumber succeeded for page {page_num}: {len(page_data['text'])} chars")
                
                with pdfplumber.open(pdf_path) as pdf:
                    page = pdf.pages[page_num - 1]
                    tables = page.extract_tables(table_settings={
                        "vertical_strategy": "lines_strict",
                        "horizontal_strategy": "lines_strict",
                        "intersection_tolerance": 5
                    })
                    if tables:
                        structured_tables = []
                        for table in tables:
                            table_df = pd.DataFrame(table[1:] if len(table) > 1 else table, columns=table[0] if table and table[0] else None)
                            table_df = table_df.replace({r'\n': ' '}, regex=True).fillna('')
                            if not table_df.empty:
                                headers = table_df.columns.tolist() if table_df.columns is not None else []
                                if headers and len(headers) >= 2 and any(keyword in ' '.join(str(h).lower() for h in headers) for keyword in ['revenue', 'profit', 'jobs', 'emission', 'procurement']):
                                    structured_tables.append({'header': headers, 'data': table_df.values.tolist()})
                                    logger.debug(f"Detected table with headers {headers} on page {page_num}")
                                else:
                                    first_col = table_df.iloc[:, 0].astype(str).str.lower() if not table_df.empty else pd.Series()
                                    if not first_col.empty and any(keyword in ' '.join(first_col) for keyword in ['revenue', 'profit', 'jobs', 'emission', 'procurement']):
                                        table_dict = table_df.set_index(table_df.columns[0]).to_dict('index') if table_df.columns is not None else {}
                                        structured_tables.append({
                                            'header': ['Key', 'Value'],
                                            'data': [[k, v] for k, row in table_dict.items() for v in row.values()]
                                        })
                                        logger.debug(f"Detected key-value table on page {page_num}")
                                    else:
                                        structured_tables.append({'header': headers, 'data': table_df.values.tolist()})
                                        logger.debug(f"Stored raw table on page {page_num}")
                        if structured_tables:
                            page_data['tables'] = structured_tables
                            logger.info(f"pdfplumber extracted {len(structured_tables)} tables for page {page_num}")
                    else:
                        logger.debug(f"No tables detected on page {page_num}")
                
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed for page {page_num}: {str(e)}")
            
            if not page_data or (not page_data['text'].strip() and not page_data['tables']):
                try:
                    page_data = pymupdf_extract.extract_pymupdf(pdf_path, page_num)
                    if page_data['text'].strip():
                        page_data['source'] = 'pymupdf'
                        logger.info(f"PyMuPDF succeeded for page {page_num}: {len(page_data['text'])} chars")
                except Exception as e:
                    logger.warning(f"PyMuPDF failed for page {page_num}: {str(e)}")
            
            if not page_data or (not page_data['text'].strip() and not page_data['tables']):
                try:
                    page_data = unstructured_extract.extract_unstructured(pdf_path, page_num)
                    if page_data['text'].strip():
                        page_data['source'] = 'unstructured'
                        logger.info(f"Unstructured.io succeeded for page {page_num}: {len(page_data['text'])} chars")
                except Exception as e:
                    logger.warning(f"Unstructured.io failed for page {page_num}: {str(e)}")
            
            if not page_data or (not page_data['text'].strip() and not page_data['tables']):
                try:
                    page_data = pytesseract_extract.extract_pytesseract(pdf_path, page_num)
                    if page_data['text'].strip():
                        page_data['source'] = 'pytesseract'
                        logger.info(f"pytesseract succeeded for page {page_num}: {len(page_data['text'])} chars")
                except Exception as e:
                    logger.warning(f"pytesseract failed for page {page_num}: {str(e)}")
            
            if not page_data or (not page_data['text'].strip() and not page_data['tables']):
                logger.warning(f"All extractors failed for page {page_num} in {pdf_path}, skipping page")
                continue
            
            extracted_data.append(page_data)
        
        if not extracted_data:
            logger.error(f"No pages successfully extracted from {pdf_path}")
            raise Exception("No pages could be extracted from the PDF")
        
        logger.info(f"Completed extraction for {pdf_path}: {len(extracted_data)}/{total_pages} pages extracted")
        return extracted_data
    
    except Exception as e:
        logger.error(f"PDF extraction failed for {pdf_path}: {str(e)}")
        raise
