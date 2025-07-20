import json
import logging
from pathlib import Path
from typing import Dict, Optional
from openai import AsyncOpenAI
from config import settings
import asyncio

"""
Classifies the sector of a document and provides sector-specific criteria.
Used for sector-specific analysis in local PDF processing.

file path: utils/sector_classifier.py
"""

logger = logging.getLogger(__name__)

class SectorClassifier:
    """
    Classifies the sector of a document and provides sector-specific criteria.

    Attributes:
        sectors_file (str): Path to sectors.json file.
        sectors_data (Dict): Loaded sector data with criteria.
        openai_client (AsyncOpenAI): Client for OpenAI API.
    """
    def __init__(self, sectors_file: str = str(Path(settings.BASE_DIR) / "data" / "sectors.json")):
        """
        Initialize the SectorClassifier with a sectors JSON file path.

        Args:
            sectors_file (str): Path to sectors.json file.
        """
        self.sectors_file = sectors_file
        self.sectors_data = self._load_sectors()
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def _load_sectors(self) -> Dict[str, Dict]:
        """
        Load sectors.json and return a dictionary of sector names to their criteria.

        Returns:
            Dict[str, Dict]: Mapping of sector names to their criteria.
        """
        try:
            with open(self.sectors_file, "r") as f:
                data = json.load(f)
            sectors = {sector["name"]: sector["criteria"] for sector in data["sectors"]}
            logger.info(f"Loaded {len(sectors)} sectors from {self.sectors_file}")
            return sectors
        except Exception as e:
            logger.error(f"Failed to load sectors.json: {str(e)}", exc_info=True)
            return {}

    async def classify(self, text: str) -> Optional[str]:
        """
        Classify the sector of the document based on its text using OpenAI.

        Args:
            text (str): Text extracted from the document.

        Returns:
            Optional[str]: Classified sector name or "Unknown" if unclassified.
        """
        logger.info("Classifying sector with OpenAI")

        sector_names = list(self.sectors_data.keys())
        prompt = (
            "You are an expert in industry classification. Analyze the following document text and determine which sector it belongs to from these options: "
            f"{', '.join(sector_names)}. Focus on key indicators such as industry-specific terms, activities, and sustainability topics. "
            "Return only the sector name (e.g., 'Agriculture, Forestry and Fishing'). If uncertain, return 'Unknown'.\n\n"
            f"Text (first 4000 characters):\n{text[:4000]}\n\nSector:"
        )

        OPENAI_SEMAPHORE = asyncio.Semaphore(10)

        for attempt in range(3):
            try:
                async with OPENAI_SEMAPHORE:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1
                    )
                sector = response.choices[0].message.content.strip().split("Sector:")[-1].strip()
                logger.info(f"Classified sector as '{sector}'")
                return sector if sector in self.sectors_data else "Unknown"
            except Exception as e:
                logger.error(f"Sector classification attempt {attempt + 1} failed: {str(e)}")
                if attempt == 2:
                    logger.error("All attempts failed, falling back to 'Unknown'")
                    return "Unknown"
                await asyncio.sleep(2 ** attempt)

        return "Unknown"

    def get_sector_criteria(self, sector: str) -> Dict[str, str]:
        """
        Return the criteria priorities for a given sector.

        Args:
            sector (str): Name of the sector.

        Returns:
            Dict[str, str]: Mapping of criteria to their priorities.
        """
        return self.sectors_data.get(sector, {})