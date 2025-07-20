"""
This file contains unit tests for the text_processing module, ensuring sentence tokenization
and embedding generation work with text from btg-pactual.pdf and handle edge cases.

file path: esg_engine/tests/test_text_processing.py
"""

import pytest
from utils.pdf_processing import extract_pdf_text
from utils.text_processing import tokenize_and_embed
from config.settings import get_settings
import os
import numpy as np

def test_tokenize_and_embed_btg_pactual():
    """
    Tests tokenization and embedding of text from btg-pactual.pdf.
    """
    settings = get_settings()
    pdf_path = os.path.join(settings["data_paths"]["reports"], "btg-pactual.pdf")
    
    if not os.path.exists(pdf_path):
        pytest.skip("btg-pactual.pdf not found in data/reports/")
    
    # Extract text from PDF
    pages = extract_pdf_text(pdf_path)
    assert len(pages) > 0, "No text extracted from PDF"
    
    # Tokenize and embed
    results = tokenize_and_embed(pages)
    
    # Verify output
    assert isinstance(results, list)
    assert len(results) > 0, "No sentences tokenized"
    assert all(isinstance(res, dict) for res in results)
    assert all("page_number" in res and "sentence_index" in res and "sentence" in res and "embedding" in res for res in results)
    assert all(isinstance(res["embedding"], np.ndarray) and res["embedding"].shape == (384,) for res in results)

def test_tokenize_and_embed_empty():
    """
    Tests handling of empty text input.
    """
    pages = [{"page_number": 1, "text": ""}]
    results = tokenize_and_embed(pages)
    assert results == []