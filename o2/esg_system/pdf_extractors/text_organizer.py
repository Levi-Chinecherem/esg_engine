import pandas as pd
import spacy
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from utils import logging, file_utils
import re
import gc

"""
File: pdf_extractors/text_organizer.py
Role: Segments extracted PDF text into ESG categories at the paragraph level for the ESG Compliance Verification System.
Key Functionality:
- Loads categories and criteria from requirements CSV (e.g., UNCTAD_requirements.csv).
- Splits page text into paragraphs and processes structured tables.
- Uses SpaCy en_core_web_sm (~12 MB, 300-dim vectors) for embeddings in batches (batch_size=16).
- Assigns paragraphs/tables to categories using embeddings and weighted keyword matching.
- Handles zero keyword matches to prevent division errors.
- Outputs a dictionary mapping categories to lists of paragraph/table data.
- Logs batch progress, model ID, and categorization results for traceability.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

class TextOrganizer:
    def __init__(self, embedding_model):
        """
        Initialize with SpaCy en_core_web_sm model for embeddings.
        
        Args:
            embedding_model (spacy.language.Language): Pre-initialized SpaCy model for embeddings.
        """
        try:
            self.model = embedding_model
            logger.info(f"Using SpaCy en_core_web_sm model for embeddings, id={id(embedding_model)}")
        except Exception as e:
            logger.error(f"Failed to initialize TextOrganizer with provided model: {str(e)}")
            raise
    
    def _extract_keywords(self, text):
        """
        Extract keywords from text, excluding generic terms and short words.
        
        Args:
            text (str): Input text (criterion or description).
        
        Returns:
            list: List of keywords (lowercase, >3 chars, non-generic).
        """
        generic_terms = {'total', 'number', 'description', 'policies', 'data', 'report', 'company', 'information', 'general'}
        words = re.findall(r'\w+', text.lower())
        return [word for word in words if len(word) > 3 and word not in generic_terms]
    
    def _generate_category_embeddings(self, requirements_df):
        """
        Generate embeddings and keywords for each category using SpaCy en_core_web_sm.
        
        Args:
            requirements_df (pd.DataFrame): DataFrame with category, criterion, description.
        
        Returns:
            tuple: (category_embeddings, category_keywords)
                - category_embeddings: Dict of category to embedding vector (300-dim).
                - category_keywords: Dict of category to weighted keywords {keyword: weight}.
        """
        categories = requirements_df['category'].unique().tolist()
        category_embeddings = {}
        category_keywords = {}
        
        for category in categories:
            # Combine criterion and description for the category
            category_rows = requirements_df[requirements_df['category'] == category]
            category_text = ' '.join(
                row['criterion'] + ' ' + row['description']
                for _, row in category_rows.iterrows()
            )
            # Generate embedding
            try:
                doc = self.model(category_text)
                category_embeddings[category] = doc.vector.tolist()
                del doc
                gc.collect()
            except Exception as e:
                logger.error(f"Error generating embedding for category {category}: {str(e)}")
                raise
            
            # Generate weighted keywords
            keywords = self._extract_keywords(category_text)
            keyword_counts = {}
            for keyword in keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            # Assign weights inversely proportional to frequency
            total_count = sum(keyword_counts.values()) or 1
            category_keywords[category] = {
                k: 1.0 / (count / total_count + 0.1) for k, count in keyword_counts.items()
            }
            logger.debug(f"Category {category}: {len(keywords)} keywords, embedding shape {len(category_embeddings[category])}")
        
        return category_embeddings, category_keywords
    
    def _split_into_paragraphs(self, text, min_length=100):
        """
        Split text into paragraphs or meaningful chunks.
        
        Args:
            text (str): Raw text from a page.
            min_length (int): Minimum character length for a paragraph.
        
        Returns:
            list: List of paragraph strings.
        """
        if not text or not text.strip():
            return []
        
        # Split on double newlines or multiple spaces
        paragraphs = re.split(r'\n{2,}|\s{4,}', text.strip())
        # Filter out short or empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) >= min_length]
        return paragraphs
    
    def _process_table_content(self, table):
        """
        Convert structured table to text for categorization.
        
        Args:
            table (dict): Table with 'header' and 'data' from pdf_extraction.py.
        
        Returns:
            str: Text representation of table (key-value pairs or header-based).
        """
        if not table or not isinstance(table, dict) or not table.get('header') or not table.get('data'):
            return ''
        
        headers = table['header']
        data = table['data']
        try:
            if headers == ['Key', 'Value']:
                # Key-value pair table
                return '\n'.join(f"{row[0]}: {row[1]}" for row in data if row and len(row) == 2 and row[0] and row[1])
            else:
                # Header-based table
                return '\n'.join(','.join(str(cell) for cell in row if cell) for row in [headers] + data if row and any(cell for cell in row))
        except Exception as e:
            logger.warning(f"Error processing table content: {str(e)}")
            return ''
    
    def _process_page_content(self, page_data):
        """
        Split page text into paragraphs and extract table content as separate units.
        
        Args:
            page_data (dict): Dictionary with 'page', 'text', 'tables', 'source'.
        
        Returns:
            list: List of tuples (content, page_num, source_type, index).
                - content: Paragraph or table text (str).
                - page_num: Page number (int).
                - source_type: 'text' or 'table_X' (str).
                - index: Paragraph or table index (int).
        """
        if not isinstance(page_data, dict) or 'page' not in page_data:
            logger.error("Invalid page_data format: 'page' key missing")
            return []
        
        page_num = page_data.get('page')
        content_units = []
        
        # Process text into paragraphs
        text = page_data.get('text', '').strip()
        paragraphs = self._split_into_paragraphs(text)
        for idx, para in enumerate(paragraphs):
            content_units.append((para, page_num, 'text', idx))
        
        # Process structured tables
        tables = page_data.get('tables', [])
        for table_idx, table in enumerate(tables):
            table_text = self._process_table_content(table)
            if table_text.strip() and len(table_text) >= 100:
                content_units.append((table_text, page_num, f'table_{table_idx + 1}', table_idx))
        
        return content_units
    
    def _compute_dynamic_threshold(self, category_counts):
        """
        Compute dynamic similarity threshold based on category distribution.
        
        Args:
            category_counts (dict): Counts of paragraphs per category.
        
        Returns:
            dict: Category-specific thresholds (lower for underrepresented categories).
        """
        total = sum(category_counts.values()) or 1
        thresholds = {}
        for category in category_counts:
            proportion = category_counts[category] / total
            if proportion < 0.1:  # Less than 10% of total
                thresholds[category] = 0.25
            elif proportion < 0.2:
                thresholds[category] = 0.35
            else:
                thresholds[category] = 0.4
        return thresholds
    
    def organize_text(self, extracted_data, requirements_csv):
        """
        Segment extracted PDF text into ESG categories at the paragraph level.
        
        Args:
            extracted_data (list): List of dictionaries with page number, text, and structured tables.
            requirements_csv (str): Path to the requirements CSV file.
        
        Returns:
            dict: Mapping of categories to lists of paragraph/table data.
        """
        try:
            # Validate inputs
            file_utils.validate_path(requirements_csv)
            if not extracted_data or not isinstance(extracted_data, list):
                logger.error("No extracted data provided or invalid format")
                raise ValueError("Extracted data is empty or not a list")
            
            # Load requirements CSV
            requirements_df = pd.read_csv(requirements_csv)
            if requirements_df.empty or not all(col in requirements_df.columns for col in ['category', 'criterion', 'description']):
                logger.error(f"Invalid requirements CSV format: {requirements_csv}")
                raise ValueError("Requirements CSV must have columns: category, criterion, description")
            
            # Initialize category buckets
            categories = requirements_df['category'].unique().tolist()
            categorized_data = {category: [] for category in categories}
            categorized_data['Uncategorized'] = []
            logger.info(f"Loaded {len(categories)} categories from {requirements_csv}: {categories}")
            
            # Generate category embeddings and keywords
            logger.info("Generating category embeddings")
            category_embeddings, category_keywords = self._generate_category_embeddings(requirements_df)
            
            # Track category distribution for dynamic thresholds
            category_counts = {category: 0 for category in categories}
            category_counts['Uncategorized'] = 0
            
            logger.info("Starting paragraph-level text organization")
            
            for page_data in extracted_data:
                content_units = self._process_page_content(page_data)
                
                if not content_units:
                    logger.debug(f"Skipping page {page_data.get('page', 'unknown')}: no valid paragraphs or tables")
                    categorized_data['Uncategorized'].append({
                        'page': page_data.get('page', 0),
                        'text': page_data.get('text', ''),
                        'tables': page_data.get('tables', []),
                        'source': page_data.get('source', 'unknown'),
                        'index': 0
                    })
                    category_counts['Uncategorized'] += 1
                    continue
                
                # Batch embeddings
                batch_size = 16
                content_texts = [content for content, _, _, _ in content_units]
                embeddings = []
                logger.info(f"Embedding {len(content_texts)} content units in batches of {batch_size}")
                for i in range(0, len(content_texts), batch_size):
                    batch_texts = content_texts[i:i + batch_size]
                    try:
                        batch_embeddings = [self.model(t).vector.tolist() for t in batch_texts]
                        embeddings.extend(batch_embeddings)
                        logger.info(f"Embedded batch {i//batch_size + 1}/{len(content_texts)//batch_size + 1} ({len(batch_texts)} units)")
                        gc.collect()
                    except Exception as e:
                        logger.error(f"Error embedding batch {i//batch_size + 1}: {str(e)}")
                        raise
                
                for idx, (content, page_num, source_type, index) in enumerate(content_units):
                    content_embedding = embeddings[idx]
                    
                    # Skip invalid embeddings
                    if np.all(np.array(content_embedding) == 0):
                        logger.warning(f"Skipping content unit {idx} on page {page_num} ({source_type}): invalid embedding")
                        categorized_data['Uncategorized'].append({
                            'page': page_num,
                            'text': content,
                            'tables': [page_data.get('tables', [])[index]] if source_type.startswith('table') else [],
                            'source': source_type,
                            'index': index
                        })
                        category_counts['Uncategorized'] += 1
                        continue
                    
                    # Calculate similarity scores
                    try:
                        similarity_scores = {
                            category: cosine_similarity(
                                np.array(content_embedding).reshape(1, -1),
                                np.array(emb).reshape(1, -1)
                            )[0][0]
                            for category, emb in category_embeddings.items()
                        }
                    except Exception as e:
                        logger.error(f"Error computing similarity scores for content on page {page_num} ({source_type}): {str(e)}")
                        categorized_data['Uncategorized'].append({
                            'page': page_num,
                            'text': content,
                            'tables': [page_data.get('tables', [])[index]] if source_type.startswith('table') else [],
                            'source': source_type,
                            'index': index
                        })
                        category_counts['Uncategorized'] += 1
                        continue
                    
                    # Keyword matching score
                    keyword_scores = {}
                    content_lower = content.lower()
                    for category, keywords in category_keywords.items():
                        score = 0
                        for keyword, weight in keywords.items():
                            if keyword in content_lower:
                                score += weight
                        keyword_scores[category] = score
                    
                    # Combine scores (70% embedding, 30% keyword)
                    max_keyword_score = max(keyword_scores.values()) if keyword_scores else 0
                    if max_keyword_score > 0:
                        combined_scores = {
                            category: 0.7 * similarity_scores[category] + 0.3 * (keyword_scores.get(category, 0) / max_keyword_score)
                            for category in categories
                        }
                    else:
                        # Skip keyword contribution if no matches
                        combined_scores = {
                            category: 0.7 * similarity_scores[category]
                            for category in categories
                        }
                        logger.debug(f"No keyword matches for content on page {page_num} ({source_type}), using similarity scores only")
                    
                    # Compute dynamic thresholds
                    thresholds = self._compute_dynamic_threshold(category_counts)
                    
                    # Assign to highest-scoring category above threshold
                    max_score = max(combined_scores.values()) if combined_scores else 0
                    assigned_category = max(combined_scores, key=combined_scores.get) if combined_scores else 'Uncategorized'
                    if max_score > thresholds.get(assigned_category, 0.4):
                        categorized_data[assigned_category].append({
                            'page': page_num,
                            'text': content,
                            'tables': [page_data.get('tables', [])[index]] if source_type.startswith('table') else [],
                            'source': source_type,
                            'index': index
                        })
                        category_counts[assigned_category] += 1
                        logger.debug(f"Paragraph/table on page {page_num} ({source_type}) assigned to {assigned_category} (score: {max_score:.3f}, threshold: {thresholds.get(assigned_category, 0.4):.3f})")
                    else:
                        categorized_data['Uncategorized'].append({
                            'page': page_num,
                            'text': content,
                            'tables': [page_data.get('tables', [])[index]] if source_type.startswith('table') else [],
                            'source': source_type,
                            'index': index
                        })
                        category_counts['Uncategorized'] += 1
                        logger.debug(f"Paragraph/table on page {page_num} ({source_type}) assigned to Uncategorized (max score: {max_score:.3f}, threshold: {thresholds.get(assigned_category, 0.4):.3f})")
            
            # Log summary
            logger.info(f"Text organization completed: {category_counts}")
            
            return categorized_data
        
        except Exception as e:
            logger.error(f"Error organizing text: {str(e)}")
            raise

def organize_text(extracted_data, requirements_csv, embedding_model=None):
    """
    Wrapper function for TextOrganizer.
    
    Args:
        extracted_data (list): List of dictionaries with page number, text, and structured tables.
        requirements_csv (str): Path to the requirements CSV file.
        embedding_model (spacy.language.Language, optional): Pre-initialized SpaCy model for embeddings.
    
    Returns:
        dict: Mapping of categories to lists of paragraph/table data.
    """
    if embedding_model is None:
        logger.error("No SpaCy model provided for text organization")
        raise ValueError("SpaCy model instance is required")
    organizer = TextOrganizer(embedding_model)
    return organizer.organize_text(extracted_data, requirements_csv)
