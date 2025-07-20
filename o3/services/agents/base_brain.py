import asyncio
import logging
from typing import List
from openai import AsyncOpenAI
import httpx
from services.models import QueryResult, SystemState
from .sub_agent import sub_agent
from .validator_agent import validator_agent
from config import settings

"""
Asynchronous base brain agent for coordinating criteria analysis.

file path: services/agents/base_brain.py
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def base_brain(state, category: str, criteria: List[str], idx: int, httpx_client: httpx.AsyncClient):
    """
    Coordinate analysis for a category of criteria.

    Args:
        state (SystemState): The system state object.
        category (str): Category of criteria (e.g., Environmental).
        criteria (List[str]): List of criteria to analyze.
        idx (int): Index for tracking the base brain task.
        httpx_client (httpx.AsyncClient): HTTP client for OpenAI requests.

    Returns:
        SystemState: Updated state with analysis results.
    """
    logger.info(f"Base Brain {idx}: Coordinating '{category}' with {len(criteria)} criteria")

    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, http_client=httpx_client)
    tasks = [
        asyncio.create_task(sub_agent(openai_client, state, criterion, state.documents[0]["id"], f"{idx}-{sub_idx}"))
        for sub_idx, criterion in enumerate(criteria)
    ]
    results = await asyncio.gather(*tasks)

    validated_tasks = [
        asyncio.create_task(validator_agent(openai_client, state, r["criterion"], r["found_info"], r["doc_id"], r["page_num"], r["similarity"], f"{idx}-{sub_idx}-v"))
        for sub_idx, r in enumerate(results) if r["found_info"]
    ]
    validated_results = await asyncio.gather(*validated_tasks)

    valid_results = [QueryResult(**r) for r in validated_results if r["found_info"]]
    state.results.extend(valid_results)
    logger.info(f"Base Brain {idx}: Processed {len(valid_results)} validated results for '{category}'")
    return state