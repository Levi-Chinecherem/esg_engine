"""
This module searches the Reports RAG Database for criteria in the ESG Engine, retrieving
target sentences with context (before, after) and metadata for extraction. It uses direct
string matching, semantic similarity, and contextual analysis with spaCy to ensure robust
matching of criteria against report content.

file path: esg_engine/agents/extraction/searcher.py
"""

import logging
import re
import spacy
from datetime import datetime
from config.settings import get_settings
from rag.reports_rag.searcher import search_report
from sentence_transformers import SentenceTransformer, util
import os
import pickle
from utils.synonyms import SYNONYMS  # Import shared synonyms

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "extraction.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Cache configuration
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".esg_engine_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Load models once at module level
model = SentenceTransformer('all-MiniLM-L6-v2')
nlp = spacy.load("en_core_web_sm")

def extract_data(report_path: str, criterion: str, description: str = None, page_texts: dict = None) -> dict:
    """
    Searches the Reports RAG for a single criterion, returning matches with context.
    Uses direct string matching, semantic similarity, and contextual analysis with spaCy.
    Falls back to description matching if provided. Uses cached page texts if provided.

    Args:
        report_path (str): Path to the report PDF.
        criterion (str): Requirement criterion to search for.
        description (str, optional): Description for fallback matching.
        page_texts (dict, optional): Cached page texts {page_number: text}.

    Returns:
        dict: Dictionary with criterion and matches (metadata, context, similarity scores).
    """
    try:
        matches = []
        similarity_threshold = 0.6
        pattern = r"(?:{})\s*[:=]?\s*([\$€£R\$]?[\d,.]+(?:\s*(?:billion|million|thousand|tCO2e|%|tons|litres|m³|kWh|MWh|hours|employees)))\b"

        # Check for cached page texts
        reports_dir = settings["data_paths"]["reports"]
        report_cache_path = os.path.join(reports_dir, f"{os.path.basename(report_path)}_texts.pkl")
        if page_texts:
            logging.info(f"Using provided cached report texts for {report_path}")
        elif os.path.exists(report_cache_path):
            with open(report_cache_path, "rb") as f:
                page_texts = pickle.load(f)
            logging.info(f"Loaded cached report texts from {report_cache_path}")
        else:
            logging.info(f"No cached texts for {report_path}, extracting")
            from utils.pdf_processing import extract_pdf_text
            documents = extract_pdf_text(report_path)
            page_texts = {doc['page_number']: doc['text'] for doc in documents}
            with open(report_cache_path, "wb") as f:
                pickle.dump(page_texts, f)
            logging.info(f"Saved report texts to {report_cache_path}")

        # Step 1: RAG search
        logging.info(f"Searching Reports RAG for criterion: {criterion}")
        rag_results = search_report([criterion], k=5)
        if rag_results:
            for res in rag_results:
                matches.append({
                    "criterion": criterion,
                    "value": res.get("sentence", "None"),
                    "source": res.get("document_name", report_path),
                    "page_number": res.get("page_number", 0),
                    "similarity": 1.0
                })
            logging.info(f"RAG found {len(matches)} matches for {criterion}")
            return {"criterion": criterion, "matches": matches}

        # Step 2: Advanced matching
        logging.info(f"No RAG matches for {criterion}, using advanced matching")
        criterion_lower = criterion.lower()
        criterion_pattern = pattern.format(re.escape(criterion_lower))
        criterion_embedding = model.encode(criterion_lower, convert_to_tensor=True)
        criterion_doc = nlp(criterion_lower)
        criterion_tokens = {token.text for token in criterion_doc if token.pos_ in ('NOUN', 'VERB', 'ADJ')}
        related_terms = set()

        for token in criterion_doc:
            for key, synonyms in SYNONYMS.items():
                if token.text in (key, *synonyms):
                    related_terms.update([key] + synonyms)
            related_terms.update([child.text for child in token.children if child.pos_ in ('NOUN', 'VERB', 'ADJ')])

        for page_number, text in page_texts.items():
            text_lower = text.lower()
            if criterion_lower in text_lower:
                regex_match = re.search(criterion_pattern, text_lower, re.IGNORECASE)
                if regex_match:
                    value = regex_match.group(1)
                    matches.append({
                        "criterion": criterion,
                        "value": value,
                        "source": report_path,
                        "page_number": page_number,
                        "similarity": 1.0
                    })
                    return {"criterion": criterion, "matches": matches}

            doc_embedding = model.encode(text, convert_to_tensor=True)
            similarity = util.cos_sim(criterion_embedding, doc_embedding).item()
            doc_nlp = nlp(text)
            doc_tokens = {token.text for token in doc_nlp if token.pos_ in ('NOUN', 'VERB', 'ADJ')}

            if (similarity > similarity_threshold or
                len(criterion_tokens.intersection(doc_tokens)) > 0 or
                any(term in text_lower for term in related_terms)):
                regex_match = re.search(criterion_pattern, text_lower, re.IGNORECASE)
                value = regex_match.group(1) if regex_match else f"Found '{criterion}' in page {page_number}"
                matches.append({
                    "criterion": criterion,
                    "value": value,
                    "source": report_path,
                    "page_number": page_number,
                    "similarity": similarity
                })

        # Step 3: Fallback to description
        if description and not matches:
            logging.info(f"Falling back to description: {description}")
            description_lower = description.lower()
            description_pattern = pattern.format(re.escape(description_lower))
            description_embedding = model.encode(description_lower, convert_to_tensor=True)
            description_doc = nlp(description_lower)
            description_tokens = {token.text for token in description_doc if token.pos_ in ('NOUN', 'VERB', 'ADJ')}
            related_terms = set()

            for token in description_doc:
                for key, synonyms in SYNONYMS.items():
                    if token.text in (key, *synonyms):
                        related_terms.update([key] + synonyms)
                related_terms.update([child.text for child in token.children if child.pos_ in ('NOUN', 'VERB', 'ADJ')])

            for page_number, text in page_texts.items():
                text_lower = text.lower()
                if description_lower in text_lower:
                    regex_match = re.search(description_pattern, text_lower, re.IGNORECASE)
                    if regex_match:
                        value = regex_match.group(1)
                        matches.append({
                            "criterion": criterion,
                            "value": value,
                            "source": report_path,
                            "page_number": page_number,
                            "similarity": 1.0
                        })
                        return {"criterion": criterion, "matches": matches}

                doc_embedding = model.encode(text, convert_to_tensor=True)
                similarity = util.cos_sim(description_embedding, doc_embedding).item()
                doc_nlp = nlp(text)
                doc_tokens = {token.text for token in doc_nlp if token.pos_ in ('NOUN', 'VERB', 'ADJ')}

                if (similarity > similarity_threshold or
                    len(description_tokens.intersection(doc_tokens)) > 0 or
                    any(term in text_lower for term in related_terms)):
                    regex_match = re.search(description_pattern, text_lower, re.IGNORECASE)
                    value = regex_match.group(1) if regex_match else f"Found description in page {page_number}"
                    matches.append({
                        "criterion": criterion,
                        "value": value,
                        "source": report_path,
                        "page_number": page_number,
                        "similarity": similarity
                    })

        logging.info(f"Found {len(matches)} matches for {criterion}")
        return {"criterion": criterion, "matches": matches}

    except Exception as e:
        logging.error(f"Extraction failed for {criterion}: {str(e)}")
        return {"criterion": criterion, "matches": []}