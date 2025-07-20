"""
This module validates extracted data against ESG standards in the ESG Engine, using advanced matching
techniques (direct string matching, semantic similarity, spaCy-based contextual analysis) to find
standard and report sentences that support each requirement criterion. It uses a precomputed standards
cache and report searches to populate standard_matches and extracted_sentences.

file path: esg_engine/agents/evaluation/validator.py
"""

import logging
import spacy
import re
from config.settings import get_settings
from rag.standards_rag.searcher import search_standards
from sentence_transformers import SentenceTransformer, util
import os
import pickle
from langchain_community.llms import FakeListLLM
import torch
from utils.synonyms import SYNONYMS  # Import shared synonyms

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "validation.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Cache configuration
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".esg_engine_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Load models
model = SentenceTransformer('all-MiniLM-L6-v2')
nlp = spacy.load("en_core_web_sm")

# Regex for numerical values (used for validation checks if needed)
VALUE_PATTERN = r"([\$€£R\$]?[\d,.]+(?:\s*(?:billion|million|thousand|tCO2e|%|tons|litres|m³|kWh|MWh|hours|employees|USD|EUR|GBP|BRL)))\b"

def validate_data(extraction: dict, standard_filter: str = None, standards_texts: dict = None, standards_cache: list = None, requirements_cache: list = None) -> dict:
    """
    Validates extracted data against ESG standards using a precomputed standards cache.
    Matches the criterion against standard clauses/sentences to populate standard_matches for standard_info.
    Uses extraction['matches'] for extracted_sentences, avoiding redundant report matching.

    Args:
        extraction (dict): Extracted data with 'criterion', 'matches', and 'source'.
        standard_filter (str, optional): Specific standard to filter (e.g., "ifrs_s1.pdf").
        standards_texts (dict, optional): Cached standards texts {filename: {page_number: text}}.
        standards_cache (list, optional): Precomputed cache of standard sentences with embeddings.
        requirements_cache (list, optional): Precomputed cache of requirements with embeddings.

    Returns:
        dict: Dictionary with criterion, standard_matches, extracted_sentences, and compliance.
    """
    try:
        criterion = extraction.get("criterion", "")
        extracted_matches = extraction.get("matches", [])
        source_file = os.path.basename(extraction.get("source", "") or "Unknown")
        if not criterion:
            logging.error("No criterion provided in extraction")
            return {"criterion": criterion, "standard_matches": [], "extracted_sentences": [], "compliance": "Failed"}

        logging.info(f"Processing criterion: {criterion}, source: {source_file}, extracted_matches: {len(extracted_matches)}")

        # Initialize results
        standard_matches = []
        extracted_sentences = []
        similarity_threshold = 0.25
        standards_dir = settings["data_paths"]["standards"]

        # Validate inputs
        standards_texts = standards_texts or {}
        standards_cache = standards_cache or []
        requirements_cache = requirements_cache or []

        # Load standards texts if not provided
        standards_text_cache_path = os.path.join(standards_dir, "texts_cache.pkl")
        if not standards_texts and os.path.exists(standards_text_cache_path):
            with open(standards_text_cache_path, "rb") as f:
                cached_texts = pickle.load(f)
                standards_texts = cached_texts.get("standards", {})

        # Step 1: Use extraction['matches'] for extracted_sentences
        for match in extracted_matches:
            sentence = match.get("text", "").strip()
            if not sentence or not isinstance(sentence, str):
                logging.warning(f"Invalid or empty sentence in extraction['matches'] for {criterion}: {match}")
                continue
            page_number = match.get("page_number", None)
            if not isinstance(page_number, int) or page_number <= 0:
                logging.warning(f"Invalid page_number {page_number} in extraction['matches']: {sentence[:50]}...")
                continue
            try:
                value_match = re.search(VALUE_PATTERN, sentence, re.IGNORECASE)
                value = value_match.group(1) if value_match else match.get("value", "None")
                source = match.get("source", source_file or "Unknown")
                similarity = match.get("similarity", 0.8)
                extracted_sentences.append({
                    "criterion": criterion,
                    "value": value,
                    "source": source,
                    "page_number": page_number,
                    "text": sentence,
                    "similarity": similarity
                })
                logging.info(f"Report match from extraction for '{criterion}': Text='{sentence}', Source={source}, Page={page_number}, Value={value}, Similarity={similarity:.2f}")
            except Exception as e:
                logging.warning(f"Failed to process extraction['matches'] sentence '{sentence[:50]}...': {str(e)}")

        # Step 2: Get criterion embedding and description
        criterion_lower = criterion.lower()
        criterion_embedding = None
        criterion_description = ""
        if requirements_cache:
            for req in requirements_cache:
                if req["criterion"].lower() == criterion_lower:
                    criterion_embedding = req["embedding"]
                    criterion_description = req["description"]
                    break
        if criterion_embedding is None or not isinstance(criterion_embedding, torch.Tensor):
            try:
                criterion_embedding = model.encode(criterion_lower, convert_to_tensor=True)
                logging.info(f"criterion embedding {criterion_embedding}")
            except Exception as e:
                logging.error(f"Failed to encode criterion '{criterion}': {str(e)}")
                return {"criterion": criterion, "standard_matches": [], "extracted_sentences": extracted_sentences, "compliance": "Failed"}

        # Step 3: Find standard sentences/clauses matching the criterion
        logging.info(f"Finding standard matches for criterion: {criterion}")
        criterion_doc = nlp(criterion_lower)
        criterion_tokens = {token.text for token in criterion_doc if token.pos_ in ('NOUN', 'VERB', 'ADJ')}
        related_terms = set(criterion_lower.split())
        for token in criterion_doc:
            for key, synonyms in SYNONYMS.items():
                if token.text in (key, *synonyms):
                    related_terms.update([key] + synonyms)
            related_terms.update([child.text for child in token.children if child.pos_ in ('NOUN', 'VERB', 'ADJ')])

        # Step 3a: FAISS-based search for standards
        rag_standards = search_standards(criterion, document_filter=standard_filter, k=30)
        logging.info(f"RAG standards found {len(rag_standards)} matches for {criterion}")
        for res in rag_standards:
            sentence = res.get("sentence", "").strip()
            if not sentence or not isinstance(sentence, str):
                logging.warning(f"Invalid or empty sentence in RAG standards result: {res}")
                continue
            page_number = res.get("page_number", None)
            if not isinstance(page_number, int) or page_number <= 0:
                logging.warning(f"Invalid page_number {page_number} for standard match: {sentence[:50]}...")
                continue
            try:
                sentence_embedding = model.encode(sentence.lower(), convert_to_tensor=True)
                similarity = util.cos_sim(criterion_embedding, sentence_embedding).item()
                if similarity > similarity_threshold:
                    standard_matches.append({
                        "standard": res["document_name"],
                        "page_number": page_number,
                        "text": sentence,
                        "similarity": similarity
                    })
                    logging.info(f"Standard match added for '{criterion}': Text='{sentence}', Source={res['document_name']}, Page={page_number}, Similarity={similarity:.2f}")
                else:
                    logging.debug(f"Standard sentence skipped for '{criterion}': Text='{sentence}', Similarity={similarity:.2f} (below threshold {similarity_threshold})")
            except Exception as e:
                logging.warning(f"Failed to compute similarity for standard sentence '{sentence[:50]}...': {str(e)}")

        # Step 3b: Advanced matching using standards_cache
        if standards_cache:
            for entry in standards_cache:
                if standard_filter and entry["filename"] != standard_filter:
                    continue
                sentence = entry.get("sentence", "").strip()
                if not sentence or not isinstance(sentence, str):
                    logging.warning(f"Invalid or empty sentence in standards_cache: {entry}")
                    continue
                page_number = entry.get("page_number", None)
                if not isinstance(page_number, int) or page_number <= 0:
                    logging.warning(f"Invalid page_number {page_number} for standard match: {sentence[:50]}...")
                    continue
                sentence_lower = sentence.lower()
                try:
                    sentence_embedding = entry.get("embedding")
                    if not isinstance(sentence_embedding, torch.Tensor):
                        sentence_embedding = model.encode(sentence_lower, convert_to_tensor=True)
                    similarity = util.cos_sim(criterion_embedding, sentence_embedding).index()
                    sentence_doc = nlp(sentence_lower)
                    sentence_tokens = {token.text for token in sentence_doc if token.pos_ in ('NOUN', 'VERB', 'ADJ')}

                    if criterion_lower in sentence_lower or (criterion_description and criterion_description.lower() in sentence_lower):
                        standard_matches.append({
                            "standard": entry["filename"],
                            "page_number": page_number,
                            "text": sentence,
                            "similarity": 1.0
                        })
                        logging.info(f"Exact standard match added for '{criterion}': Text='{sentence}', Source={entry['filename']}, Page={page_number}, Similarity=1.0")
                        continue

                    token_overlap = len(criterion_tokens.intersection(sentence_tokens))
                    term_matches = sum(1 for term in related_terms if term in sentence_lower)
                    if similarity > similarity_threshold or token_overlap >= 1 or term_matches >= 1:
                        standard_matches.append({
                            "standard": entry["filename"],
                            "page_number": page_number,
                            "text": sentence,
                            "similarity": max(similarity, (token_overlap + term_matches) * 0.15)
                        })
                        logging.info(f"Standard match added for '{criterion}': Text='{sentence}', Source={entry['filename']}, Page={page_number}, Similarity={max(similarity, (token_overlap + term_matches) * 0.15):.2f}, Tokens={token_overlap}, Terms={term_matches}")
                    else:
                        logging.debug(f"Standards cache sentence skipped for '{criterion}': Text='{sentence}', Similarity={similarity:.2f}, Tokens={token_overlap}, Terms={term_matches}")
                except Exception as e:
                    logging.warning(f"Failed to process standards_cache entry '{sentence[:50]}...': {str(e)}")

        # Step 3c: Fallback to standards_texts
        if not standard_matches and standards_texts:
            logging.info(f"Performing fallback matching for {criterion} in standards texts")
            for filename, pages in standards_texts.items():
                if standard_filter and filename != standard_filter:
                    continue
                for page_number, text in pages.items():
                    if not isinstance(page_number, int) or page_number <= 0:
                        logging.warning(f"Invalid page_number {page_number} in standards_texts: {filename}")
                        continue
                    if not text.strip():
                        logging.warning(f"Empty text for {filename}, page {page_number}")
                        continue
                    doc_nlp = nlp(text.lower())
                    sentences = [sent.text.strip() for sent in doc_nlp.sents if sent.text.strip()]
                    for idx, sentence in enumerate(sentences):
                        sentence_lower = sentence.lower()
                        try:
                            sentence_embedding = model.encode(sentence_lower, convert_to_tensor=True)
                            similarity = util.cos_sim(criterion_embedding, sentence_embedding).item()
                            if criterion_lower in sentence_lower or (criterion_description and criterion_description.lower() in sentence_lower):
                                standard_matches.append({
                                    "standard": filename,
                                    "page_number": page_number,
                                    "text": sentence,
                                    "similarity": 1.0
                                })
                                logging.info(f"Exact fallback standard match added for '{criterion}': Text='{sentence}', Source={filename}, Page={page_number}, Index={idx}, Similarity=1.0")
                                continue
                            sentence_doc = nlp(sentence_lower)
                            sentence_tokens = {token.text for token in sentence_doc if token.pos_ in ('NOUN', 'VERB', 'ADJ')}
                            token_overlap = len(criterion_tokens.intersection(sentence_tokens))
                            term_matches = sum(1 for term in related_terms if term in sentence_lower)
                            if similarity > similarity_threshold or token_overlap >= 1 or term_matches >= 1:
                                standard_matches.append({
                                    "standard": filename,
                                    "page_number": page_number,
                                    "text": sentence,
                                    "similarity": max(similarity, (token_overlap + term_matches) * 0.15)
                                })
                                logging.info(f"Fallback standard match added for '{criterion}': Text='{sentence}', Source={filename}, Page={page_number}, Index={idx}, Similarity={max(similarity, (token_overlap + term_matches) * 0.15):.2f}, Tokens={token_overlap}, Terms={term_matches}")
                            else:
                                logging.debug(f"Fallback standard sentence skipped for '{criterion}': Text='{sentence}', Similarity={similarity:.2f}, Tokens={token_overlap}, Terms={term_matches}")
                        except Exception as e:
                            logging.warning(f"Failed to process standards_texts sentence '{sentence[:50]}...': {str(e)}")

        # Sort and limit matches
        standard_matches = sorted(standard_matches, key=lambda x: x["similarity"], reverse=True)[:10]
        extracted_sentences = sorted(extracted_sentences, key=lambda x: x["similarity"], reverse=True)[:10]
        logging.info(f"Final results for '{criterion}': {len(standard_matches)} standard matches, {len(extracted_sentences)} report matches")
        if standard_matches:
            logging.info(f"Standard matches for '{criterion}': {[f'Text={m['text']}, Source={m['standard']}, Page={m['page_number']}, Similarity={m['similarity']:.2f}' for m in standard_matches]}")
        if extracted_sentences:
            logging.info(f"Report matches for '{criterion}': {[f'Text={m['text']}, Source={m['source']}, Page={m['page_number']}, Value={m['value']}, Similarity={m['similarity']:.2f}' for m in extracted_sentences]}")

        # Step 4: Evaluate compliance
        compliance = "Non-compliant"
        if extracted_sentences and standard_matches:
            llm = FakeListLLM(responses=["Compliant"])
            prompt = f"""
            Validate if the criterion '{criterion}' is met by the extracted report data:
            Extracted data: {extracted_sentences}
            Supported by standard sentences: {standard_matches}
            Determine compliance by checking if the extracted data aligns with the standard requirements.
            """
            try:
                compliance = llm.invoke(prompt)
                logging.info(f"Compliance for '{criterion}': {compliance}")
            except Exception as e:
                logging.warning(f"LangChain evaluation failed for '{criterion}': {str(e)}")
        elif not extracted_sentences:
            logging.warning(f"No report matches for '{criterion}', marking as Non-compliant")
        elif not standard_matches:
            logging.warning(f"No standard matches for '{criterion}', marking as Non-compliant")

        result = {
            "criterion": criterion,
            "standard_matches": standard_matches,
            "extracted_sentences": extracted_sentences,
            "compliance": compliance
        }

        logging.info(f"Validation complete for '{criterion}': Compliance={compliance}, Standard matches={len(standard_matches)}, Report matches={len(extracted_sentences)}")
        return result

    except Exception as e:
        logging.error(f"Validation failed for '{criterion}': {str(e)}")
        return {"criterion": criterion, "standard_matches": [], "extracted_sentences": extracted_sentences, "compliance": "Failed"}