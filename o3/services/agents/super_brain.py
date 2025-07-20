import asyncio
import psutil
import numpy as np
import logging
import json
from typing import Optional
from pathlib import Path
import faiss
import nltk
from sklearn.metrics.pairwise import cosine_similarity

from config import settings, INDEX_PATH, faiss_index
from utils.pdf_parser import DocumentParser
from utils.text_analyzer import MinimumRequirementAnalyzer
from utils.criteria_loader import load_criteria
from utils.sector_classifier import SectorClassifier
from utils.standards_manager import StandardsManager
from services.classifier import ReportClassifier
from services.models import SystemState

"""
Asynchronous super brain agent for initializing state and loading criteria.

file path: services/agents/super_brain.py
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def super_brain(state):
    """
    Initialize state, classify report type and sector, and load IFRS standards.

    Args:
        state (SystemState): The system state object containing document data.

    Returns:
        SystemState: Updated state with classified report type, sector, and criteria, or None on failure.
    """
    logger.info("Super Brain: Starting analysis")

    resource_usage = psutil.virtual_memory().percent + psutil.cpu_percent(interval=1) / 2
    state.resource_usage = resource_usage
    logger.info(f"Current resource usage: {resource_usage}%")

    all_pages = []
    for doc in state.documents:
        for page_num, page_text in enumerate(doc["pages"], 1):
            all_pages.append({"page": page_num, "text": page_text})
    all_text = " ".join(page["text"] for page in all_pages)
    if not all_text.strip():
        logger.error("Super Brain: No text extracted from document.")
        return None

    state.chunks = DocumentParser().split_into_chunks(all_text, chunk_size=4096)
    logger.info(f"Super Brain: Split into {len(state.chunks)} chunks")

    analyzer = MinimumRequirementAnalyzer()
    for page in all_pages:
        sentences = nltk.sent_tokenize(page["text"])
        for sentence in sentences:
            state.sentences.append({
                "content": sentence,
                "page": page["page"]
            })
    logger.info(f"Super Brain: Split into {len(state.sentences)} sentences")

    embeddings = await analyzer.vectorize_chunks([s["content"] for s in state.sentences])
    state.sentence_embeddings = np.array(embeddings, dtype=np.float32)
    
    logger.info(f"FAISS index dimension: {faiss_index.d}, Embedding dimension: {state.sentence_embeddings.shape[1]}")
    faiss_index.add(state.sentence_embeddings)
    faiss.write_index(faiss_index, str(INDEX_PATH))
    logger.info(f"Super Brain: Indexed {len(state.sentences)} sentences")

    criteria = load_criteria()
    classifier = ReportClassifier()
    state.report_type = await classifier.classify(all_text)
    logger.info(f"Super Brain: Detected report type '{state.report_type}'")

    sector_classifier = SectorClassifier()
    detected_sector = await sector_classifier.classify(all_text)
    logger.info(f"Super Brain: Detected sector '{detected_sector}'")
    sector_criteria_dict = sector_classifier.get_sector_criteria(detected_sector)

    sectors_json_path = Path(__file__).parent.parent.parent / "data" / "sectors.json"
    try:
        with open(sectors_json_path, "r") as f:
            sector_data = json.load(f)
        sector_names = [s["name"] for s in sector_data["sectors"]]
        logger.info(f"Loaded sector data from {sectors_json_path} with {len(sector_names)} sectors")
    except Exception as e:
        logger.error(f"Failed to load sectors.json: {str(e)}")
        raise

    if not sector_criteria_dict or detected_sector not in sector_names:
        logger.warning(f"Super Brain: No exact match for sector '{detected_sector}' in {sector_names}")
        sector_embeddings = await analyzer.vectorize_chunks(sector_names)
        detected_embedding = await analyzer.vectorize_chunks([detected_sector])
        similarities = cosine_similarity(np.array(detected_embedding), np.array(sector_embeddings))[0]
        best_match_idx = np.argmax(similarities)
        best_match = sector_names[best_match_idx]
        similarity_score = similarities[best_match_idx]
        if similarity_score > 0.7:
            state.sector = best_match
            state.sector_criteria = next(s["criteria"] for s in sector_data["sectors"] if s["name"] == best_match)
            logger.info(f"Super Brain: Semantically matched '{detected_sector}' to '{best_match}' (similarity: {similarity_score:.2f})")
        else:
            logger.error(f"Super Brain: No close semantic match for '{detected_sector}' (max similarity: {similarity_score:.2f})")
            raise ValueError(f"No viable sector match for '{detected_sector}'")
    else:
        state.sector = detected_sector
        state.sector_criteria = sector_criteria_dict

    logger.info(f"Super Brain: Loaded {len(state.sector_criteria)} criteria for sector '{state.sector}'")

    state.type_criteria = criteria.get(state.report_type, {})
    state.base_criteria = criteria.get("base", {})
    total_criteria = sum(len(crits) for crits in state.base_criteria.values())
    max_agents = min(total_criteria, max(1, int((settings.MAX_RESOURCE_USAGE - resource_usage) / 5)))
    state.active_agents = max_agents
    logger.info(f"Super Brain: Allocating {max_agents} agents for {total_criteria} criteria")

    state.standards_manager = StandardsManager()
    await state.standards_manager.initialize()
    asyncio.create_task(state.standards_manager.monitor())
    logger.info("Super Brain: Initialized StandardsManager with IFRS knowledge base")

    return state