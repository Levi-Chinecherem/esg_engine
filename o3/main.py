import os
import logging
import asyncio
from pathlib import Path
from services.core import process_minimum_requirements
from services.agents.super_brain import super_brain
from services.agents.base_brain import base_brain
from services.agents.summarizer import summarizer
import httpx

"""
Main orchestrator for the Sustainability Reports Analyzer, coordinating PDF processing and analysis.
Processes all PDFs in data/input/, generates analysis results, and saves them as CSV files in data/output/.

file path: main.py
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """
    Main function to process all PDFs in the input directory.
    """
    input_dir = Path("data/input")
    pdf_files = list(input_dir.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files to process")

    for pdf_path in pdf_files:
        logger.info(f"Processing {pdf_path.name}")
        state = await process_minimum_requirements(str(pdf_path), output_mode="file", original_filename=pdf_path.name)
        if not state:
            logger.error(f"Failed to initialize state for {pdf_path.name}")
            continue

        # Continue processing with super_brain, using 'criterion' column from UNCTAD_datapoints.csv
        state = await super_brain(state, criteria_name="criterion")
        if not state:
            logger.error(f"Super brain failed for {pdf_path.name}")
            continue

        # Process criteria
        async with httpx.AsyncClient() as httpx_client:
            tasks = [
                asyncio.create_task(base_brain(state, cat, crits, idx, httpx_client))
                for idx, (cat, crits) in enumerate(state.base_criteria.items())
            ]
            logger.info(f"Scheduled {len(tasks)} base_brain tasks for {pdf_path.name}")
            await asyncio.gather(*tasks)

        # Summarize and save to CSV
        await summarizer(state, pdf_path.name)
        logger.info(f"Completed processing for {pdf_path.name}")

if __name__ == "__main__":
    asyncio.run(main())