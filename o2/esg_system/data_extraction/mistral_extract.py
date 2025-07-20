import pandas as pd
from utils import logging, file_utils
import re

"""
File: esg_system/data_extraction/mistral_extract.py
Role: Extracts specific data points from categorized text using rule-based logic.
Key Functionality:
- Processes categorized text from text_organizer.py for each ESG criterion.
- Extracts full paragraph or table text for Extracted_Value.
- Uses regex and keyword matching to extract values, units, and page numbers.
- Outputs a dictionary mapping criteria to extracted data with full text.
- Logs extraction attempts and errors for traceability.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

class MistralExtractor:
    def __init__(self):
        """
        Initialize without a model for rule-based extraction.
        """
        try:
            logger.info("Initialized MistralExtractor with rule-based logic")
        except Exception as e:
            logger.error(f"Failed to initialize MistralExtractor: {str(e)}")
            raise

    def extract_data(self, categorized_data, requirements_csv):
        """
        Extract data for each criterion from categorized text using rule-based logic.
        
        Args:
            categorized_data (dict): Dictionary mapping categories to lists of paragraph/table data.
            requirements_csv (str): Path to the requirements CSV file.
        
        Returns:
            list: List of dictionaries with criterion, value, unit, page, category, text, source, index, tables.
        """
        try:
            file_utils.validate_path(requirements_csv)
            if not categorized_data:
                logger.error("No categorized data provided for extraction")
                raise ValueError("Categorized data is empty")
            
            requirements_df = pd.read_csv(requirements_csv)
            if requirements_df.empty or not all(col in requirements_df.columns for col in ['category', 'criterion', 'description']):
                logger.error(f"Invalid requirements CSV format: {requirements_csv}")
                raise ValueError("Requirements CSV must have columns: category, criterion, description")
            
            extracted_data = []
            
            for _, row in requirements_df.iterrows():
                criterion = row['criterion']
                category = row['category']
                description = row['description']
                
                relevant_text = []
                sources = []
                tables = []
                for item in categorized_data.get(category, []) + categorized_data.get('Uncategorized', []):
                    text = item.get('text', '')
                    if text.strip():
                        relevant_text.append(text)
                        sources.append({'page': item['page'], 'source': item.get('source', 'text'), 'index': item.get('index', 0)})
                        if item.get('source', '').startswith('table_'):
                            tables.append(item.get('table_data', {}))
                
                if not relevant_text:
                    logger.warning(f"No relevant text found for criterion {criterion} in category {category}")
                    extracted_data.append({
                        'criterion': criterion,
                        'value': None,
                        'unit': None,
                        'page': None,
                        'category': category,
                        'text': '',
                        'source': 'none',
                        'index': 0,
                        'tables': []
                    })
                    continue
                
                value = None
                unit = None
                page = None
                source = 'none'
                index = 0
                extracted_text = ''
                
                for text, src in zip(relevant_text, sources):
                    text_lower = text.lower()
                    description_lower = description.lower()
                    
                    if criterion.lower() in text_lower or any(keyword in text_lower for keyword in description_lower.split() if len(keyword) > 3):
                        extracted_text = text
                        page = src['page']
                        source = src['source']
                        index = src['index']
                        
                        # Numeric value and unit
                        numeric_match = re.search(r'(\d+\.?\d*)\s*(usd|mt co2e|%|employees|hours|m3)\b', text, re.IGNORECASE)
                        if numeric_match:
                            value = numeric_match.group(1)
                            unit = numeric_match.group(2).upper()
                            break
                        # Non-numeric criteria
                        elif 'disclosure' in description_lower or 'policy' in description_lower:
                            value = 'Disclosed'
                            unit = 'N/A'
                            break
                
                extracted_data.append({
                    'criterion': criterion,
                    'value': value,
                    'unit': unit,
                    'page': page,
                    'category': category,
                    'text': extracted_text,
                    'source': source,
                    'index': index,
                    'tables': tables
                })
                logger.debug(f"Extracted data for {criterion}: value={value}, unit={unit}, page={page}, source={source}")
            
            logger.info(f"Completed data extraction: {len(extracted_data)} criteria processed")
            return extracted_data
        
        except Exception as e:
            logger.error(f"Data extraction failed for {requirements_csv}: {str(e)}")
            raise

def extract_data(categorized_data, requirements_csv, embedding_model=None):
    """
    Wrapper function for MistralExtractor.
    
    Args:
        categorized_data (dict): Dictionary mapping categories to lists of paragraph/table data.
        requirements_csv (str): Path to the requirements CSV file.
        embedding_model (spacy.language.Language, optional): Not used in rule-based extraction.
    
    Returns:
        list: List of dictionaries with extracted data.
    """
    extractor = MistralExtractor()
    return extractor.extract_data(categorized_data, requirements_csv)
