from typing import List, Optional
from pathlib import Path
from datetime import UTC, datetime
from utils.report_builder import ReportGenerator
from services.models import SystemState
import logging
import re
from openai import AsyncOpenAI
from config import settings

"""
Asynchronous summarizer agent for generating and saving analysis reports.

file path: services/agents/summarizer.py
"""

logger = logging.getLogger(__name__)

def clean_found_info(found_info: List[str]) -> List[str]:
    """
    Clean found_info entries by removing Markdown asterisks and numbered prefixes, preserving relevance tags.

    Args:
        found_info (List[str]): List of raw found_info strings.

    Returns:
        List[str]: Cleaned list with each entry starting with '--'.
    """
    cleaned_info = []
    for info in found_info:
        logger.debug(f"Cleaning found_info: {info}")
        # Remove numbered prefixes (e.g., '1.1.', '1.2.')
        info = re.sub(r'^\d+\.\d+\.\s*', '', info)
        # Remove Markdown asterisks (e.g., '**...**', '*')
        info = re.sub(r'\*+', '', info)
        # Clean up GRI references (add spaces, e.g., '3-3GRI' → '3-3 GRI')
        info = re.sub(r'(\d+)-(\d+)(GRI)', r'\1-\2 \3', info)
        cleaned_info.append(f"-- {info.strip()}")
    return cleaned_info

async def _generate_sali_ai_summary(results: List[dict], api_key: str) -> str:
    """
    Generate a SALI AI summary of analysis results by Source_Page using GPT, batching pages.

    Args:
        results (List[dict]): List of result dictionaries.
        api_key (str): OpenAI API key.

    Returns:
        str: SALI AI summary grouped by Source_Page.
    """
    try:
        client = AsyncOpenAI(api_key=api_key)
        # Group findings by Source_Page
        page_findings = {}
        for result in results:
            for info, page in zip(result["found_info"], result["page_num"]):
                if "Error:" in info or "Not processed:" in info:
                    continue
                page = str(page)
                if page not in page_findings:
                    page_findings[page] = []
                page_findings[page].append({
                    "criterion": result["criterion"],
                    "status": result["status"],
                    "verified_result": result["verified_result"],
                    "found_info": info
                })

        summaries = []
        batch_size = 5  # Process 5 pages per batch
        page_keys = sorted(page_findings.keys())
        for i in range(0, len(page_keys), batch_size):
            batch_pages = page_keys[i:i + batch_size]
            prompt = "Summary by SALI AI:\nSummarize the following ESG analysis results by page in a concise, human-readable format, removing any Markdown formatting:\n"
            total_tokens = len(prompt) // 4  # Rough estimate: 1 token ~ 4 chars
            for page in batch_pages:
                findings = page_findings[page]
                page_text = f"Page {page}:\n"
                for finding in findings:  # Include all findings
                    finding_text = (
                        f"Criterion: {finding['criterion']}\n"
                        f"Status: {finding['status']}\n"
                        f"Verified Result: {finding['verified_result']}\n"
                        f"Details: {finding['found_info']}\n\n"
                    )
                    finding_tokens = len(finding_text) // 4
                    if total_tokens + finding_tokens > 120000:  # Buffer below 128000
                        logger.warning(f"Stopping batch at page {page} to avoid token limit")
                        break
                    page_text += finding_text
                    total_tokens += finding_tokens
                prompt += page_text

            logger.info(f"Batch {i//batch_size + 1} estimated tokens: {total_tokens}")
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000  # Increased for more findings
            )
            # Remove Markdown from GPT output
            summary = re.sub(r'\*+', '', response.choices[0].message.content.strip())
            summaries.append(summary)

        return "\n\n".join(summaries) if summaries else "Summary generation failed."
    except Exception as e:
        logger.error(f"Failed to generate SALI AI summary: {str(e)}")
        return "Summary generation failed."

async def summarizer(state: SystemState, original_filename: Optional[str] = None):
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

        # Log base_criteria for debugging
        logger.info(f"Base criteria structure: {state.base_criteria}")

        # Generate SALI AI summary
        sali_ai_summary = await _generate_sali_ai_summary(cleaned_results, settings.OPENAI_API_KEY)

        generator = ReportGenerator(Path(settings.OUTPUT_DIR))
        report = generator.generate_report(
            analysis_results=cleaned_results,
            categories=state.base_criteria,
            report_type=state.report_type,
            document_name=original_filename or f"unknown_pdf_{state.documents[0]['id']}",
            audit_date=datetime.now(UTC).strftime("%Y-%m-%d")
        )

        pdf_name = original_filename.rsplit(".", 1)[0] if original_filename else f"unknown_pdf_{state.documents[0]['id']}"
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        generator._generate_csv_report(
            report=report,
            filename=f"{pdf_name}_{timestamp}",
            document_name=original_filename or f"unknown_pdf_{state.documents[0]['id']}",
            audit_date=datetime.now(UTC).strftime("%Y-%m-%d"),
            sali_ai_summary=sali_ai_summary
        )
        logger.info(f"Summarizer: CSV generated for {original_filename} as {pdf_name}_{timestamp}.csv")
    except Exception as e:
        logger.error(f"Summarizer: Error: {str(e)}", exc_info=True)