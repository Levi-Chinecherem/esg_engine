import asyncio
import psutil
import numpy as np
import logging
import json
import re
from typing import List, Dict, Optional
from utils.report_builder import ReportGenerator
from openai import AsyncOpenAI
import httpx
import nltk
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import process
import faiss
import datetime
from pathlib import Path
from datetime import UTC

from config import settings, INDEX_PATH, faiss_index
from utils.pdf_parser import DocumentParser
from utils.text_analyzer import MinimumRequirementAnalyzer
from utils.criteria_loader import load_criteria
from utils.sector_classifier import SectorClassifier
from utils.standards_manager import StandardsManager
from services.classifier import ReportClassifier
from services.models import QueryResult, SystemState

"""
Asynchronous agents for processing minimum requirements analysis.
Coordinates document analysis, criteria evaluation, and validation.

file path: services/agents.py
"""

nltk.download('punkt', quiet=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

OPENAI_SEMAPHORE = asyncio.Semaphore(5)

def clean_found_info(found_info: List[str]) -> List[str]:
    """
    Clean found_info entries by removing Markdown tags and numbered prefixes, retaining 'Sentence X:', and formatting with hyphens.

    Args:
        found_info (List[str]): List of raw found_info strings with Markdown and numbering.

    Returns:
        List[str]: Cleaned list with each entry starting with '-' and retaining 'Sentence X:'.
    """
    cleaned_info = []
    for info in found_info:
        # Remove numbered prefixes (e.g., '1.1.', '1.2.')
        info = re.sub(r'^\d+\.\d+\.\s*', '', info)
        # Remove Markdown bold tags (e.g., '**...**') but keep 'Sentence X:'
        info = re.sub(r'\*\*(Sentence \d+:)\s*\*\*', r'\1', info)
        # Clean up GRI references (add spaces for readability, e.g., '3-3GRI' → '3-3 GRI')
        info = re.sub(r'(\d+)-(\d+)(GRI)', r'\1-\2 \3', info)
        # Ensure the sentence and [relevant/partial/irrelevant: ...] are preserved
        if ' - [relevant:' in info or ' - [partial:' in info or ' - [irrelevant:' in info:
            cleaned_info.append(f"- {info.strip()}")
        else:
            # Handle unexpected formats
            cleaned_info.append(f"- {info.strip()} [irrelevant: Unrecognized format]")
    return cleaned_info

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

    sectors_json_path = Path(__file__).parent.parent / "data" / "sectors.json"
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
    logger.info(f"Sub-agent {idx}: Processing '{criterion}' for '{state.report_type}' in sector '{state.sector}'")

    type_specific = state.type_criteria.get(criterion.split(" - ")[0], {}).get(criterion, None)
    if type_specific and type_specific["additional_terms"] == ["not relevant"] and type_specific["description"] == "not relevant":
        logger.info(f"Sub-agent {idx}: Skipping '{criterion}' as not relevant to '{state.report_type}'")
        return {
            "criterion": criterion,
            "found_info": [f"Not processed: Criterion is not relevant to {state.report_type}"],
            "doc_id": doc_id,
            "page_num": [],
            "similarity": 0.0,
            "status": "✗",
            "verified_result": "Not Applicable",
            "relevance": "Not Applicable",
            "percentage": 0.0
        }

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
            "verified_result": "No evidence",
            "relevance": state.sector_criteria.get(criterion, ""),
            "percentage": 0.0
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
        "verified_result": "No evidence",
        "relevance": state.sector_criteria.get(criterion, ""),
        "percentage": 0.0
    }

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
    logger.info(f"Validator-agent {idx}: Validating '{criterion}' for '{state.report_type}' in sector '{state.sector}'")

    type_specific = state.type_criteria.get(criterion.split(" - ")[0], {}).get(criterion, None)
    if type_specific and type_specific["additional_terms"] == ["not relevant"] and type_specific["description"] == "not relevant":
        logger.info(f"Validator-agent {idx}: '{criterion}' is not relevant to '{state.report_type}'")
        return {
            "criterion": criterion,
            "found_info": [f"Not processed: Criterion is not relevant to {state.report_type}"],
            "doc_id": doc_id,
            "page_num": page_num,
            "similarity": similarity,
            "status": "✗",
            "verified_result": "Not Applicable",
            "relevance": "Not Applicable",
            "percentage": 0.0
        }

    sector_priority = state.sector_criteria.get(criterion)
    relevance_to_percentage = {"High": 100.0, "Medium": 75.0, "Low": 50.0, "Not Applicable": 0.0}

    if sector_priority is None:
        logger.warning(f"Validator-agent {idx}: No direct match for '{criterion}' in sector '{state.sector}' criteria")
        available_criteria = list(state.sector_criteria.keys())
        best_match, score = process.extractOne(criterion, available_criteria)
        if score > 80:
            sector_priority = state.sector_criteria[best_match]
            logger.info(f"Validator-agent {idx}: Fuzzy matched '{criterion}' to '{best_match}' (score: {score})")
        else:
            logger.error(f"Validator-agent {idx}: No close match for '{criterion}' (best: '{best_match}', score: {score})")
            sector_priority = None

    if sector_priority is None:
        relevance = ""
        default_percentage = 0.0
        status = "✗"
    else:
        relevance = sector_priority
        default_percentage = relevance_to_percentage.get(sector_priority, 0.0)
        status = "✓" if sector_priority in ["High", "Medium", "Low"] else "✗"
        logger.info(f"Validator-agent {idx}: Sector priority for '{criterion}' is '{sector_priority}'")

    if sector_priority == "Not Applicable":
        logger.info(f"Validator-agent {idx}: '{criterion}' is explicitly not applicable to sector '{state.sector}'")
        return {
            "criterion": criterion,
            "found_info": [f"Not applicable: Criterion is explicitly not relevant to '{state.sector}' sector."],
            "doc_id": doc_id,
            "page_num": page_num,
            "similarity": similarity,
            "status": "✗",
            "verified_result": "Not Applicable",
            "relevance": "Not Applicable",
            "percentage": 0.0
        }

    if not found_info or all("Error:" in info or "No relevant data" in info for info in found_info):
        logger.info(f"Validator-agent {idx}: No usable info for '{criterion}'")
        return {
            "criterion": criterion,
            "found_info": ["No relevant data found."],
            "doc_id": doc_id,
            "page_num": page_num,
            "similarity": similarity,
            "status": status,
            "verified_result": "No evidence",
            "relevance": relevance,
            "percentage": default_percentage
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
        f"You are an expert validator for a '{state.report_type}' report in the '{state.sector}' sector, focusing on {report_focus}. "
        f"Using the full knowledge base (IFRS S1, S2, etc.), evaluate these findings for '{criterion}':\n"
        f"Knowledge Base Context:\n{ifrs_context}\n\n"
        f"Sector Priority: {sector_priority or 'None'} (High=100%, Medium=75%, Low=50%, Not Applicable=0%).\n"
        f"Validate each sentence and assign:\n"
        f"- Status: '✓' if High/Medium/Low, '✗' if Not Applicable or missing.\n"
        f"- Relevance: Exact sector priority ('{sector_priority or ''}').\n"
        f"- Percentage: 100% (High), 75% (Medium), 50% (Low), 0% (Not Applicable), scaled by evidence.\n"
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
            evidence_score = relevant_count + 0.5 * partial_count
            max_percentage = relevance_to_percentage.get(sector_priority, 0.0)
            
            if evidence_score >= 5:
                percentage = max_percentage
            elif evidence_score > 0:
                percentage = round((evidence_score / 5) * max_percentage, 2)
            else:
                percentage = default_percentage
            
            logger.info(f"Validator-agent {idx}: Validated {len(validated_info)} findings for '{criterion}' "
                       f"(relevant: {relevant_count}, partial: {partial_count}, percentage: {percentage}%)")
            break
        except Exception as e:
            logger.error(f"Validator-agent {idx}: Validation failed, attempt {attempt + 1}: {str(e)}")
            if attempt == 2:
                validated_info = [f"Validation Error: {str(e)}"]
                verified_result = "Validation Error"
                percentage = default_percentage
            await asyncio.sleep(4 ** attempt)

    return {
        "criterion": criterion,
        "found_info": validated_info,
        "doc_id": doc_id,
        "page_num": page_num,
        "similarity": similarity,
        "status": status,
        "verified_result": verified_result,
        "relevance": relevance,
        "percentage": percentage
    }

async def summarizer(state, original_filename: Optional[str] = None):
    """
    Generate and save the analysis report as a CSV file.

    Args:
        state (SystemState): The system state object with analysis results.
        original_filename (str): Original name of the PDF file.

    Returns:
        None
    """
    logger.info("Summarizer: Generating report")
    try:
        # Clean the found_info field for each result
        cleaned_results = []
        for result in state.results:
            cleaned_result = result.dict()
            cleaned_result["found_info"] = clean_found_info(cleaned_result["found_info"])
            cleaned_results.append(cleaned_result)

        generator = ReportGenerator(Path(settings.OUTPUT_DIR))
        report = generator.generate_report(
            cleaned_results,
            state.base_criteria,
            state.report_type,
            state.type_criteria,
            state.sector_criteria
        )

        pdf_name = original_filename.rsplit(".", 1)[0] if original_filename else f"unknown_pdf_{state.documents[0]['id']}"
        timestamp = datetime.datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{pdf_name}_{timestamp}"
        generator._generate_csv_report(report, csv_filename)
        logger.info(f"Summarizer: CSV generated for {original_filename} as {csv_filename}.csv")
    except Exception as e:
        logger.error(f"Summarizer: Error: {str(e)}", exc_info=True)