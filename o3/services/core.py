import os
import logging
from typing import List
import asyncio
import httpx

from utils.pdf_parser import DocumentParser
from services.models import SystemState, QueryResult  # Import from models.py

"""
Core processing logic for analyzing PDF documents for minimum requirements.
Handles text extraction, analysis, and report generation for local testing.

file path: services/core.py
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def process_minimum_requirements(pdf_path: str, output_mode: str, original_filename: str):
    """
    Process a PDF file for minimum requirements analysis and save results as CSV.

    Args:
        pdf_path (str): Path to the PDF file.
        output_mode (str): Output mode (set to 'file' for CSV output).
        original_filename (str): Original name of the PDF file.

    Returns:
        None
    """
    logger.info(f"Starting processing for PDF at {pdf_path}")
    
    state = SystemState(documents=[], output_mode=output_mode)

    # Validate PDF file
    if not pdf_path.endswith(".pdf"):
        logger.error(f"Invalid file {pdf_path}: must be a PDF")
        return

    # Check if file exists
    if not os.path.exists(pdf_path):
        logger.error(f"File not found at {pdf_path}")
        return

    # Extract text using DocumentParser
    parser = DocumentParser()
    with open(pdf_path, "rb") as f:
        pages = parser.parse_document([f])
    
    if not any(page.strip() for page in pages) or pages == ["No readable content"]:
        logger.error(f"Failed to extract text from {original_filename}")
        return

    doc_id = hash(pdf_path)
    state.documents.append({"id": doc_id, "pages": pages, "title": original_filename})
    logger.info(f"Loaded {len(pages)} pages from {pdf_path}")

    return state  # Return state for further processing in main.py