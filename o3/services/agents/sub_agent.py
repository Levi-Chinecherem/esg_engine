import asyncio
import logging
import nltk
import numpy as np
from typing import List
from openai import AsyncOpenAI
from sklearn.metrics.pairwise import cosine_similarity

from config import settings
from utils.text_analyzer import MinimumRequirementAnalyzer
from services.models import SystemState

"""
Asynchronous sub-agent for analyzing individual criteria.

file path: services/agents/sub_agent.py
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

OPENAI_SEMAPHORE = asyncio.Semaphore(5)

nltk.download('punkt', quiet=True)

async def sub_agent(openai_client: AsyncOpenAI, state, criterion: str, doc_id: int, idx: str):
    """
    Analyze a single criterion against the document.

    Args:
        openai_client (AsyncOpenAI): OpenAI client for analysis.
        state (SystemState): The system state object.
        criterion (str): The criterion to analyze.
        doc_id (int): Document identifier.
        idx (str): Index for tracking the sub-agent task.

    Returns:
        dict: Analysis result for the criterion.
    """
    logger.info(f"Sub-agent {idx}: Processing '{criterion}' for '{state.report_type}'")

    analyzer = MinimumRequirementAnalyzer()
    criterion_embedding = (await analyzer.vectorize_chunks([criterion]))[0]
    criterion_embedding_np = np.array([criterion_embedding], dtype=np.float32)

    similarities = cosine_similarity(criterion_embedding_np, state.sentence_embeddings)[0]
    candidate_indices = np.argsort(similarities)[-100:][::-1]
    candidates = [
        {"score": similarities[i], "metadata": state.sentences[i]}
        for i in candidate_indices if similarities[i] > 0.6
    ]
    logger.info(f"Sub-agent {idx}: Found {len(candidates)} candidates for '{criterion}', max similarity={max(similarities):.4f}")

    if not candidates:
        return {
            "criterion": criterion,
            "found_info": ["No relevant data found."],
            "doc_id": doc_id,
            "page_num": [],
            "similarity": 0.0,
            "status": "✗",
            "verified_result": "No evidence"
        }

    found_info = []
    page_nums = set()
    context = [c["metadata"]["content"] for c in candidates]
    batch_size = 20

    for i in range(0, len(context), batch_size):
        batch = context[i:i + batch_size]
        prompt = (
            f"You are an expert in sustainability reporting (GRI, SASB, TCFD). Evaluate each sentence for relevance to '{criterion}' "
            f"in the context of a '{state.report_type}' report. Focus on intent and material topics. "
            f"Return all potentially relevant sentences in this exact format: 'Sentence X: [sentence] - [why it matches]'.\n\n"
            f"Sentences:\n" + "\n".join(f"- {s}" for s in batch) + "\n\nSummary:"
        )
        for attempt in range(3):
            try:
                async with OPENAI_SEMAPHORE:
                    response = await openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.0,
                        seed=42
                    )
                summary = response.choices[0].message.content.strip()
                batch_info = [line.strip("- ").strip() for line in summary.split("\n") if "Sentence" in line and line.strip()]
                if batch_info:
                    found_info.extend(batch_info)
                    for match in candidates[i:i + batch_size]:
                        if any(match["metadata"]["content"] in info for info in batch_info):
                            page_nums.add(match["metadata"]["page"])
                break
            except Exception as e:
                logger.error(f"Sub-agent {idx}: Error for '{criterion}' batch {i//batch_size + 1}, attempt {attempt + 1}: {str(e)}")
                if attempt == 2:
                    found_info.append(f"Error: {str(e)}")
                await asyncio.sleep(4 ** attempt)

    if found_info and not any("Error:" in info for info in found_info):
        logger.info(f"Sub-agent {idx}: Found info for '{criterion}': {found_info}")

    similarity = max([c["score"] for c in candidates] + [0.0]) if candidates else 0.0
    return {
        "criterion": criterion,
        "found_info": found_info if found_info else ["No relevant data found."],
        "doc_id": doc_id,
        "page_num": sorted(list(page_nums)),
        "similarity": similarity,
        "status": "✗",
        "verified_result": "No evidence"
    }