import logging
from typing import List, Dict
import numpy as np
from utils.standards_manager import StandardsManager

"""
Data models for ESG analysis.

file path: services/models.py
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

class QueryResult:
    """
    Represents the result of analyzing a criterion in a document.

    Attributes:
        criterion (str): The criterion being analyzed.
        found_info (List[str]): List of relevant text snippets found.
        doc_id (int): Document identifier.
        page_num (List[int]): List of page numbers where info was found.
        similarity (float): Similarity score of the match.
        status (str): Status of the criterion (✓ or ✗).
        verified_result (str): Verification result (e.g., IFRS S1, No evidence).
    """
    def __init__(self, criterion: str, found_info: List[str], doc_id: int, page_num: List[int], similarity: float, status: str, verified_result: str):
        self.criterion = criterion
        self.found_info = found_info
        self.doc_id = doc_id
        self.page_num = page_num
        self.similarity = similarity
        self.status = status
        self.verified_result = verified_result

    def dict(self):
        """
        Convert QueryResult to dictionary for report generation.

        Returns:
            dict: Dictionary representation of the QueryResult.
        """
        return {
            "criterion": self.criterion,
            "found_info": self.found_info,
            "doc_id": self.doc_id,
            "page_num": self.page_num,
            "similarity": self.similarity,
            "status": self.status,
            "verified_result": self.verified_result
        }

class SystemState:
    """
    Holds the state of the analysis process.

    Attributes:
        documents (List[dict]): List of documents with their pages and metadata.
        report_type (str): Type of report (e.g., esg_report).
        results (List[QueryResult]): List of analysis results.
        resource_usage (float): System resource usage percentage.
        active_agents (int): Number of active analysis agents.
        output_mode (str): Output mode (e.g., file).
        chunks (List[str]): Text chunks from the document.
        sentences (List[dict]): Sentence metadata (content, page).
        sentence_embeddings (np.ndarray): Embeddings of sentences.
        base_criteria (Dict): Base criteria for analysis.
        standards_manager (StandardsManager): Manager for IFRS standards.
    """
    def __init__(self, documents: List[dict], output_mode: str):
        self.documents = documents
        self.report_type = ""
        self.results = []
        self.resource_usage = 0.0
        self.active_agents = 0
        self.output_mode = output_mode
        self.chunks = []
        self.sentences = []
        self.sentence_embeddings = None
        self.base_criteria = {}
        self.standards_manager = None