import asyncio
import psutil
import numpy as np
import logging
import nltk
from typing import Optional
from pathlib import Path
import faiss

from config import settings, INDEX_PATH, faiss_index
from utils.pdf_parser import DocumentParser
from utils.text_analyzer import MinimumRequirementAnalyzer
from utils.criteria_loader import load_criteria
from utils.standards_manager import StandardsManager
from services.classifier import ReportClassifier
from services.models import SystemState

"""
Asynchronous super brain agent for initializing state and loading criteria.

file path: services/agents/super_brain.py
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

nltk.download('punkt', quiet=True)

async def super_brain(state, criteria_name: str = "criterion"):
    """
    Initialize state, classify report type, and load UNCTAD criteria.

    Args:
        state (SystemState): The system state object containing document data.
        criteria_name (str): Column name in UNCTAD_datapoints.csv for criteria (default: "indicator_name").

    Returns:
        SystemState: Updated state with classified report type and criteria, or None on failure.
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

    criteria = load_criteria(criteria_name=criteria_name)
    classifier = ReportClassifier()
    state.report_type = await classifier.classify(all_text)
    logger.info(f"Super Brain: Detected report type '{state.report_type}'")

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
