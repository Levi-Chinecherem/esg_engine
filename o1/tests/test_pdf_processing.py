"""
Tests for PDF processing functionality in the ESG Engine.

file path: esg_engine/tests/test_pdf_processing.py
"""

import pytest
import os
from config.settings import get_settings
from utils.pdf_processing import extract_pdf_text
import time

def test_extract_pdf_text_btg_pactual():
    """
    Tests extracting text from btg-pactual.pdf.
    """
    settings = get_settings()
    pdf_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")

    # Check if PDF exists
    if not os.path.exists(pdf_path):
        pytest.skip("btg-pactual.pdf not found in data/reports/")

    pages = extract_pdf_text(pdf_path)

    # Verify output structure
    assert isinstance(pages, list)
    assert len(pages) > 0  # Assume PDF has at least one page with text
    assert all(isinstance(page, dict) for page in pages)
    assert all("page_number" in page and "text" in page for page in pages)
    assert all(isinstance(page["page_number"], int) and isinstance(page["text"], str) for page in pages)

    # Check performance (increased to 60 seconds)
    start_time = time.time()
    extract_pdf_text(pdf_path)
    assert time.time() - start_time < 60, "PDF processing took too long"

def test_extract_pdf_text_missing():
    """
    Tests handling of missing PDF files.
    """
    with pytest.raises(FileNotFoundError):
        extract_pdf_text("nonexistent.pdf")

def test_extract_pdf_text_empty(tmp_path):
    """
    Tests handling of empty PDF files.
    """
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(b"")
    pages = extract_pdf_text(str(pdf_path))
    assert pages == []