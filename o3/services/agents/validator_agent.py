import asyncio
import logging
from typing import List
from openai import AsyncOpenAI
from services.models import SystemState

"""
Asynchronous validator agent for validating criteria analysis results.

file path: services/agents/validator_agent.py
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

OPENAI_SEMAPHORE = asyncio.Semaphore(5)

async def validator_agent(openai_client: AsyncOpenAI, state, criterion: str, found_info: List[str], doc_id: int, page_num: List[int], similarity: float, idx: str):
    """
    Validate analysis results for a criterion using OpenAI and IFRS standards.

    Args:
        openai_client (AsyncOpenAI): OpenAI client for validation.
        state (SystemState): The system state object.
        criterion (str): The criterion being validated.
        found_info (List[str]): List of found text snippets.
        doc_id (int): Document identifier.
        page_num (List[int]): List of page numbers.
        similarity (float): Similarity score.
        idx (str): Index for tracking the validator agent.

    Returns:
        dict: Validated analysis result.
    """
    logger.info(f"Validator-agent {idx}: Validating '{criterion}' for '{state.report_type}'")

    if not found_info or all("Error:" in info or "No relevant data" in info for info in found_info):
        logger.info(f"Validator-agent {idx}: No usable info for '{criterion}'")
        return {
            "criterion": criterion,
            "found_info": ["No relevant data found."],
            "doc_id": doc_id,
            "page_num": page_num,
            "similarity": similarity,
            "status": "✗",
            "verified_result": "No evidence"
        }

    ifrs_matches = await state.standards_manager.query(criterion)
    ifrs_context = "\n".join([f"{m['source']}: {m['chunk']}" for m in ifrs_matches])

    report_focus = {
        "financial_report": "financial performance, revenue, profit, and economic outcomes",
        "esg_report": "environmental, social, and governance metrics (e.g., emissions, diversity, ethics)",
        "sustainability_report": "holistic sustainability efforts across environmental and social domains",
        "annual_report": "financials, strategy, operational overview, and governance",
        "csr_report": "community impact, ethical practices, and social responsibility"
    }.get(state.report_type, "general sustainability topics")

    prompt = (
        f"You are an expert validator for a '{state.report_type}' report, focusing on {report_focus}. "
        f"Using the full knowledge base (IFRS S1, S2, etc.), evaluate these findings for '{criterion}':\n"
        f"Knowledge Base Context:\n{ifrs_context}\n\n"
        f"Validate each sentence and assign:\n"
        f"- Status: '✓' if evidence is found, '✗' if no relevant evidence.\n"
        f"- Verified Result: List all matches (IFRS S1, IFRS S2, CEO Statement, External Verification by [source], Defined Criteria), no prefix.\n"
        f"Mark sentences:\n"
        f"- 'relevant: [why, e.g., IFRS S1 para X, IFRS S2, CEO, External by Y, Criteria]' if fully compliant.\n"
        f"- 'partial: [why]' if incomplete.\n"
        f"- 'irrelevant: [why]' if no match.\n"
        f"Return format: 'Sentence X: [sentence] - [relevant/partial/irrelevant: why]'\n\n"
        f"Findings:\n" + "\n".join(f"- {f}" for f in found_info) + "\n\nValidated:"
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
            validated = response.choices[0].message.content.strip()
            validated_info = [line.strip("- ").strip() for line in validated.split("\n") if "Sentence" in line and line.strip()]
            
            if not validated_info:
                validated_info = [
                    f"Sentence {i+1}: {info.split(' - ', 1)[0]} - [relevant: Assumed relevant due to presence]"
                    for i, info in enumerate(found_info) if "Error:" not in info and "Not processed:" not in info
                ]
            
            verifications = []
            for info in validated_info:
                info_lower = info.lower()
                if "ifrs s1" in info_lower:
                    verifications.append("IFRS S1")
                if "ifrs s2" in info_lower:
                    verifications.append("IFRS S2")
                if "ceo" in info_lower or "chief executive" in info_lower:
                    verifications.append("CEO Statement")
                if "external" in info_lower and "by " in info_lower:
                    source = info.split("by ")[-1].split(" - ")[0]
                    verifications.append(f"External Verification by {source}")
                if "criteria" in info_lower:
                    verifications.append("Defined Criteria")

            verified_result = ", ".join(sorted(set(verifications))) if verifications else "No evidence"
            
            relevant_count = sum(1 for info in validated_info if "relevant:" in info.lower())
            partial_count = sum(1 for info in validated_info if "partial:" in info.lower())
            status = "✓" if (relevant_count + partial_count) > 0 else "✗"
            
            logger.info(f"Validator-agent {idx}: Validated {len(validated_info)} findings for '{criterion}' "
                       f"(relevant: {relevant_count}, partial: {partial_count})")
            break
        except Exception as e:
            logger.error(f"Validator-agent {idx}: Validation failed, attempt {attempt + 1}: {str(e)}")
            if attempt == 2:
                validated_info = [f"Validation Error: {str(e)}"]
                verified_result = "Validation Error"
                status = "✗"
            await asyncio.sleep(4 ** attempt)

    return {
        "criterion": criterion,
        "found_info": validated_info,
        "doc_id": doc_id,
        "page_num": page_num,
        "similarity": similarity,
        "status": status,
        "verified_result": verified_result
    }