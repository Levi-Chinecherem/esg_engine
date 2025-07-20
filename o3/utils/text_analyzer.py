import asyncio
import torch
import numpy as np
import logging
from transformers import AutoTokenizer, AutoModel
from typing import List

"""
Singleton class for generating text embeddings using a pre-trained transformer model.
Used for vectorizing text chunks for similarity analysis.

file path: utils/text_analyzer.py
"""

logger = logging.getLogger(__name__)

class MinimumRequirementAnalyzer:
    """
    Singleton class for generating text embeddings using a pre-trained transformer model.
    """
    _instance = None

    def __new__(cls):
        """
        Implement singleton pattern to ensure only one instance exists.

        Returns:
            MinimumRequirementAnalyzer: The single instance of the class.
        """
        if cls._instance is None:
            cls._instance = super(MinimumRequirementAnalyzer, cls).__new__(cls)
            torch.manual_seed(42)
            torch.cuda.manual_seed_all(42) if torch.cuda.is_available() else None
            cls._instance.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            cls._instance.model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            cls._instance.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            cls._instance.model.to(cls._instance.device)
            cls._instance.model.eval()
        return cls._instance

    async def vectorize_chunks(self, chunks: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of text chunks using the transformer model.

        Args:
            chunks (List[str]): List of text chunks to vectorize.

        Returns:
            np.ndarray: Array of embeddings with shape (n_chunks, embedding_dim).
        """
        logger.info(f"Vectorizing {len(chunks)} chunks")
        embeddings = []
        batch_size = 32

        if torch.cuda.is_available():
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                embedding = outputs.last_hidden_state[:, 0, :].detach().cpu().numpy()
            
            embeddings.extend(embedding)
            del inputs, outputs
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        result = np.array(embeddings)
        logger.info(f"Generated embeddings with shape {result.shape}")
        return result