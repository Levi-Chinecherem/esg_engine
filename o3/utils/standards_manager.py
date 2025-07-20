import os
import asyncio
import logging
from pathlib import Path
import faiss
import numpy as np
from watchgod import awatch
from config import settings
from utils.pdf_parser import DocumentParser
from utils.text_analyzer import MinimumRequirementAnalyzer
import json
from typing import List, Dict

"""
Manages IFRS standards in a FAISS index for persistent semantic search.
Used to query standards for validation in analysis.

file path: utils/standards_manager.py
"""

logger = logging.getLogger(__name__)

class StandardsManager:
    """
    Manages IFRS standards in a FAISS index for persistent semantic search.

    Attributes:
        base_dir (Path): Directory containing IFRS standard PDFs.
        index_path (Path): Path to the FAISS index file.
        metadata_path (Path): Path to the metadata JSON file.
        dimension (int): Dimension of the embeddings (384).
        parser (DocumentParser): Parser for extracting text from PDFs.
        analyzer (MinimumRequirementAnalyzer): Analyzer for generating embeddings.
        index (faiss.IndexFlatL2): FAISS index for semantic search.
        metadata (List[Dict]): Metadata for indexed chunks.
    """
    def __init__(self, base_dir: str = str(Path(settings.BASE_DIR) / "data" / "base")):
        """
        Initialize the StandardsManager with a base directory.

        Args:
            base_dir (str): Directory containing IFRS standard PDFs.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.index_path = self.base_dir / "faiss_index"
        self.metadata_path = self.base_dir / "metadata.json"
        self.dimension = 384
        self.parser = DocumentParser()
        self.analyzer = MinimumRequirementAnalyzer()
        self.index = None
        self.metadata = []

    async def initialize(self):
        """
        Initialize the FAISS index and load or build it.
        """
        self.index = self._init_index()
        await self._load_or_build_index()

    def _init_index(self) -> faiss.IndexFlatL2:
        """
        Initialize or load the FAISS index.

        Returns:
            faiss.IndexFlatL2: Initialized FAISS index.
        """
        if self.index_path.exists():
            index = faiss.read_index(str(self.index_path))
            logger.info(f"Loaded FAISS index from {self.index_path}")
        else:
            index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"Created new FAISS index")
        return index

    async def _load_or_build_index(self):
        """
        Load existing index/metadata or build from scratch if not present.
        """
        if self.metadata_path.exists() and self.index_path.exists():
            with open(self.metadata_path, "r") as f:
                self.metadata = json.load(f)
            logger.info(f"Loaded {len(self.metadata)} metadata entries")
        else:
            await self._rebuild_index()

    async def _rebuild_index(self):
        """
        Rebuild FAISS index from PDFs in data/base/ asynchronously.
        """
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        embeddings = []

        for pdf_file in self.base_dir.glob("*.pdf"):
            logger.info(f"Processing standard {pdf_file}")
            with open(pdf_file, "rb") as f:
                pages = self.parser.parse_document([f])
            text = " ".join(pages)
            chunks = self.parser.split_into_chunks(text, chunk_size=512)
            
            chunk_embeddings = await self.analyzer.vectorize_chunks(chunks)

            for chunk, embedding in zip(chunks, chunk_embeddings):
                self.metadata.append({"source": pdf_file.name, "chunk": chunk})
                embeddings.append(embedding)

        if embeddings:
            embeddings_np = np.array(embeddings, dtype=np.float32)
            self.index.add(embeddings_np)
            faiss.write_index(self.index, str(self.index_path))
            with open(self.metadata_path, "w") as f:
                json.dump(self.metadata, f)
            logger.info(f"Built FAISS index with {len(embeddings)} chunks")
        else:
            logger.warning("No standards found in data/base/ to build FAISS index")

    async def query(self, text: str, top_k: int = 5) -> List[Dict]:
        """
        Query the FAISS index for relevant IFRS standards.

        Args:
            text (str): Text to query against the index.
            top_k (int): Number of top results to return (default: 5).

        Returns:
            List[Dict]: List of matching standards with source, chunk, and distance.
        """
        try:
            embedding = (await self.analyzer.vectorize_chunks([text]))[0]
            embedding_np = np.array([embedding], dtype=np.float32)
            distances, indices = self.index.search(embedding_np, top_k)
            results = [
                {"source": self.metadata[i]["source"], "chunk": self.metadata[i]["chunk"], "distance": float(d)}
                for i, d in zip(indices[0], distances[0]) if i >= 0
            ]
            logger.debug(f"Queried FAISS for '{text[:50]}...': {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"FAISS query failed for '{text[:50]}...': {str(e)}")
            return []

    async def monitor(self):
        """
        Monitor the base directory for changes and rebuild the index if PDFs are modified.
        """
        logger.info(f"Starting file monitoring on {self.base_dir}")
        async for changes in awatch(str(self.base_dir)):
            for change_type, path in changes:
                if path.endswith(".pdf"):
                    logger.info(f"Detected {change_type} in {path}")
                    await self._rebuild_index()
                    break