"""
This module provides functionality to extract text from PDF files page by page for the ESG Engine.
It uses pdfplumber as the primary library, with fallbacks to pypdf, pymupdf, and pytesseract (OCR)
to handle complex or scanned PDFs, ensuring robust text extraction.

file path: esg_engine/utils/pdf_processing.py
"""

import os
import logging
from config.settings import get_settings
from utils.resource_monitor import check_resources
import pdfplumber
import pypdf
import fitz  # pymupdf
import pytesseract
from PIL import Image
import io

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "errors.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configure Tesseract path (adjust if needed for your system)
try:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
except Exception as e:
    logging.warning(f"Tesseract not configured: {str(e)}. OCR will be skipped.")

def extract_pdf_text(pdf_path):
    """
    Extracts text from a PDF file page by page, using pdfplumber, pypdf, pymupdf, and pytesseract (OCR)
    as fallbacks. Returns a list of dictionaries with page numbers and text.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        list: List of dictionaries with keys 'page_number' (int) and 'text' (str).

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        Exception: For other PDF processing errors, logged to errors.log.
    """
    # Check if file exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Check resources before processing
    if not check_resources()["compliant"]:
        logging.error(f"Resource usage exceeds limit, aborting PDF processing for {pdf_path}")
        return []

    pages = []
    try:
        # Try pdfplumber first
        logging.info(f"Attempting pdfplumber extraction for {pdf_path}")
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logging.info(f"Total pages in {pdf_path}: {total_pages}")
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append({"page_number": page_num, "text": text})
                    logging.info(f"Extracted text from page {page_num}/{total_pages} with pdfplumber: {text[:100]}...")
                else:
                    logging.warning(f"Empty page {page_num}/{total_pages} with pdfplumber in {pdf_path}")
                    # Try fallbacks
                    text = try_fallback_extraction(pdf_path, page_num)
                    if text.strip():
                        pages.append({"page_number": page_num, "text": text})
                        logging.info(f"Extracted text from page {page_num}/{total_pages} with fallback: {text[:100]}...")
                    else:
                        logging.warning(f"Page {page_num}/{total_pages} empty after all fallbacks in {pdf_path}")

        logging.info(f"pdfplumber extracted {len(pages)}/{total_pages} pages from {pdf_path}")
        return pages

    except Exception as e:
        logging.error(f"pdfplumber failed for {pdf_path}: {str(e)}")
        # Try fallbacks for all pages
        return try_fallback_extraction(pdf_path)

def try_fallback_extraction(pdf_path, page_num=None):
    """
    Attempts text extraction using pypdf, pymupdf, and pytesseract as fallbacks.

    Args:
        pdf_path (str): Path to the PDF file.
        page_num (int, optional): Specific page to extract. If None, process all pages.

    Returns:
        str or list: Extracted text for a single page, or list of page dictionaries for all pages.
    """
    # Single page mode
    if page_num is not None:
        # Try pypdf
        try:
            logging.info(f"Attempting pypdf extraction for page {page_num} in {pdf_path}")
            with open(pdf_path, "rb") as file:
                reader = pypdf.PdfReader(file)
                if page_num <= len(reader.pages):
                    text = reader.pages[page_num - 1].extract_text() or ""
                    if text.strip():
                        return text
                    logging.warning(f"Empty page {page_num} with pypdf in {pdf_path}")
        except Exception as e:
            logging.error(f"pypdf failed for page {page_num} in {pdf_path}: {str(e)}")

        # Try pymupdf
        try:
            logging.info(f"Attempting pymupdf extraction for page {page_num} in {pdf_path}")
            doc = fitz.open(pdf_path)
            if page_num <= doc.page_count:
                page = doc.load_page(page_num - 1)
                text = page.get_text("text") or ""
                if text.strip():
                    doc.close()
                    return text
                logging.warning(f"Empty page {page_num} with pymupdf in {pdf_path}")
            doc.close()
        except Exception as e:
            logging.error(f"pymupdf failed for page {page_num} in {pdf_path}: {str(e)}")

        # Try pytesseract (OCR)
        try:
            logging.info(f"Attempting pytesseract OCR for page {page_num} in {pdf_path}")
            doc = fitz.open(pdf_path)
            if page_num <= doc.page_count:
                page = doc.load_page(page_num - 1)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Increase resolution
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img, lang="eng") or ""
                doc.close()
                if text.strip():
                    return text
                logging.warning(f"Empty page {page_num} with pytesseract in {pdf_path}")
            doc.close()
        except Exception as e:
            logging.error(f"pytesseract failed for page {page_num} in {pdf_path}: {str(e)}")
            if "tesseract is not installed" in str(e).lower():
                logging.warning("Tesseract OCR not installed or not in PATH. Install Tesseract to enable OCR.")

        return ""

    # All pages mode
    pages = []
    try:
        # Try pypdf
        logging.info(f"Attempting pypdf extraction for all pages in {pdf_path}")
        with open(pdf_path, "rb") as file:
            reader = pypdf.PdfReader(file)
            total_pages = len(reader.pages)
            logging.info(f"Total pages in {pdf_path}: {total_pages}")
            for page_num in range(1, total_pages + 1):
                text = reader.pages[page_num - 1].extract_text() or ""
                if text.strip():
                    pages.append({"page_number": page_num, "text": text})
                    logging.info(f"Extracted text from page {page_num}/{total_pages} with pypdf: {text[:100]}...")
                else:
                    logging.warning(f"Empty page {page_num}/{total_pages} with pypdf in {pdf_path}")

        if pages:
            logging.info(f"pypdf extracted {len(pages)}/{total_pages} pages from {pdf_path}")
            return pages

    except Exception as e:
        logging.error(f"pypdf failed for {pdf_path}: {str(e)}")

    try:
        # Try pymupdf
        logging.info(f"Attempting pymupdf extraction for all pages in {pdf_path}")
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        logging.info(f"Total pages in {pdf_path}: {total_pages}")
        for page_num in range(1, total_pages + 1):
            page = doc.load_page(page_num - 1)
            text = page.get_text("text") or ""
            if text.strip():
                pages.append({"page_number": page_num, "text": text})
                logging.info(f"Extracted text from page {page_num}/{total_pages} with pymupdf: {text[:100]}...")
            else:
                logging.warning(f"Empty page {page_num}/{total_pages} with pymupdf in {pdf_path}")
        doc.close()

        if pages:
            logging.info(f"pymupdf extracted {len(pages)}/{total_pages} pages from {pdf_path}")
            return pages

    except Exception as e:
        logging.error(f"pymupdf failed for {pdf_path}: {str(e)}")

    try:
        # Try pytesseract (OCR)
        logging.info(f"Attempting pytesseract OCR for all pages in {pdf_path}")
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        logging.info(f"Total pages in {pdf_path}: {total_pages}")
        for page_num in range(1, total_pages + 1):
            page = doc.load_page(page_num - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Increase resolution
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang="eng") or ""
            if text.strip():
                pages.append({"page_number": page_num, "text": text})
                logging.info(f"Extracted text from page {page_num}/{total_pages} with pytesseract: {text[:100]}...")
            else:
                logging.warning(f"Empty page {page_num}/{total_pages} with pytesseract in {pdf_path}")
        doc.close()

        logging.info(f"pytesseract extracted {len(pages)}/{total_pages} pages from {pdf_path}")
        return pages

    except Exception as e:
        logging.error(f"pytesseract failed for {pdf_path}: {str(e)}")
        if "tesseract is not installed" in str(e).lower():
            logging.warning("Tesseract OCR not installed or not in PATH. Install Tesseract to enable OCR.")
        return []