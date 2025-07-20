import asyncio
import logging
import re
from typing import List, Optional
from pathlib import Path
from datetime import UTC, datetime
from utils.report_builder import ReportGenerator
from services.models import QueryResult, SystemState
from config import settings

"""
Asynchronous summarizer agent for generating and saving analysis reports.

file path: services/agents/summarizer.py
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_found_info(found_info: List[str]) -> List[str]:
    """
    Clean found_info entries by removing all Markdown asterisks, numbered prefixes, and formatting with double hyphens.

    Args:
        found_info (List[str]): List of raw found_info strings with Markdown and numbering.

    Returns:
        List[str]: Cleaned list with each entry starting with '--' and retaining 'Sentence X:'.
    """
    cleaned_info = []
    for info in found_info:
        # Remove numbered prefixes (e.g., '1.1.', '1.2.')
        info = re.sub(r'^\d+\.\d+\.\s*', '', info)
        # Remove all Markdown asterisks (e.g., '**...**', '*')
        info = re.sub(r'\*+', '', info)
        # Clean up GRI references (add spaces, e.g., '3-3GRI' → '3-3 GRI')
        info = re.sub(r'(\d+)-(\d+)(GRI)', r'\1-\2 \3', info)
        # Ensure the sentence and [relevant/partial/irrelevant: ...] are preserved
        if ' - [relevant:' in info or ' - [partial:' in info or ' - [irrelevant:' in info:
            cleaned_info.append(f"-- {info.strip()}")
        else:
            # Handle unexpected formats
            cleaned_info.append(f"-- {info.strip()} [irrelevant: Unrecognized format]")
    return cleaned_info

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
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{pdf_name}_{timestamp}"
        generator._generate_csv_report(report, csv_filename)
        logger.info(f"Summarizer: CSV generated for {original_filename} as {csv_filename}.csv")
    except Exception as e:
        logger.error(f"Summarizer: Error: {str(e)}", exc_info=True)