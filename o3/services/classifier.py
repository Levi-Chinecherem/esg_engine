import logging
from openai import AsyncOpenAI
import asyncio
from config import settings

"""
Classifies the type of a report (e.g., Annual, ESG) using OpenAI's GPT model.
Handles report type classification for local PDF analysis.

file path: services/classifier.py
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

class ReportClassifier:
    """
    Classifies the type of a report using OpenAI's GPT model.

    Attributes:
        openai_client (AsyncOpenAI): Client for OpenAI API.
    """
    def __init__(self):
        """
        Initialize the ReportClassifier with OpenAI client.
        """
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def classify(self, text: str) -> str:
        """
        Classify the report type based on provided text using OpenAI.

        Args:
            text (str): Text extracted from the report to classify.

        Returns:
            str: Classified report type (e.g., "financial_report", "esg_report") or "base" on failure.
        """
        logger.info("Classifying report type with OpenAI")
        
        prompt = (
            "You are an expert in corporate reporting. Analyze the following document text and determine its report type from these options: "
            "Annual Report, ESG Report, Sustainability Report, Financial Report, CSR Report. "
            "Consider key indicators: Annual Reports focus on financials and strategy; ESG Reports emphasize GRI/SASB metrics; "
            "Sustainability Reports narrate holistic sustainability; Financial Reports prioritize profit/loss; CSR Reports focus on community/ethics. "
            "Return only the report type name (e.g., 'ESG Report').\n\n"
            f"Text (first 4000 characters):\n{text[:4000]}\n\nReport Type:"
        )

        # Semaphore to control concurrent OpenAI requests
        OPENAI_SEMAPHORE = asyncio.Semaphore(10)

        for attempt in range(3):
            try:
                async with OPENAI_SEMAPHORE:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1
                    )
                report_type = response.choices[0].message.content.strip().split("Report Type:")[-1].strip()
                logger.info(f"Classified as '{report_type}'")
                return report_type.lower().replace(" ", "_")
            except Exception as e:
                logger.error(f"Classification attempt {attempt + 1} failed: {str(e)}")
                if attempt == 2:
                    logger.error("Falling back to 'base'")
                    return "base"
                await asyncio.sleep(2 ** attempt)
        
        return "base"