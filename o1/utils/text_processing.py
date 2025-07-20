"""
This module provides text processing functionality for the ESG Engine, including sentence
tokenization using spaCy and embedding generation using sentence-transformers. It processes
text with metadata for use in RAG databases.

file path: esg_engine/utils/text_processing.py
"""

import spacy
from sentence_transformers import SentenceTransformer
import numpy as np
from config.settings import get_settings

# Load settings
settings = get_settings()

# Initialize spaCy and sentence-transformers models
nlp = spacy.load(settings["model_params"]["spacy_model"])
model = SentenceTransformer(settings["model_params"]["sentence_transformer_model"])

def tokenize_and_embed(pages):
    """
    Tokenizes text into sentences and generates embeddings, preserving metadata.
    
    Args:
        pages (list): List of dictionaries with 'page_number' (int) and 'text' (str).
    
    Returns:
        list: List of dictionaries with 'page_number', 'sentence_index', 'sentence', and 'embedding'.
    """
    results = []
    
    # Process each page
    for page in pages:
        page_num = page["page_number"]
        text = page["text"]
        
        # Skip empty text
        if not text.strip():
            continue
            
        # Tokenize into sentences
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        # Generate embeddings
        embeddings = model.encode(sentences, convert_to_numpy=True) if sentences else []
        
        # Store results with metadata
        for idx, (sentence, embedding) in enumerate(zip(sentences, embeddings)):
            results.append({
                "page_number": page_num,
                "sentence_index": idx,
                "sentence": sentence,
                "embedding": embedding
            })
    
    return results