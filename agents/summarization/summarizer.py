"""
This module generates human-readable summaries for the ESG Engine, combining extracted data,
standards, and requirements using LangChain.

file path: esg_engine/agents/summarization/summarizer.py
"""

import logging
from config.settings import get_settings
# Placeholder for LangChain
from langchain_community.llms import FakeListLLM
import os

# Configure logging
settings = get_settings()
log_file = os.path.join(settings["data_paths"]["output"], "summarization.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def generate_summary(extraction, validation, requirement):
    """
    Generates a human-readable summary for a criterion using LangChain.
    
    Args:
        extraction (dict): Extracted data with criterion and matches.
        validation (dict): Validation result with standard matches and compliance.
        requirement (dict): Requirement with category, criterion, description.
    
    Returns:
        str: Human-readable summary.
    """
    try:
        criterion = requirement["criterion"]
        llm = FakeListLLM(responses=[f"Summary for {criterion}: {'Compliant' if validation['compliance'] == 'Compliant' else 'Non-compliant'} based on {len(extraction.get('matches', []))} matches and {len(validation.get('standard_matches', []))} standards."])
        prompt = f"Summarize compliance for '{criterion}': Extraction: {extraction.get('matches', [])}; Validation: {validation}; Requirement: {requirement}"
        summary = llm.invoke(prompt)
        
        logging.info(f"Generated summary for {criterion}")
        return summary
    
    except Exception as e:
        logging.error(f"Summary generation failed for {criterion}: {str(e)}")
        return f"Failed to generate summary for {criterion}"