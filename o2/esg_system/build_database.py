import os
import pdfplumber
import pandas as pd
import chromadb
import spacy
from utils import logging, file_utils
from config import Config
import argparse
import hashlib
import pickle
import re
import numpy as np
import gc
import psutil

"""
File: esg_system/build_database.py
Role: Initializes ChromaDB with standards and requirements for the ESG Compliance Verification System.
Key Functionality:
- Processes standards PDFs into paragraphs for embedding.
- Embeds paragraphs using lightweight SpaCy en_core_web_sm model (~12 MB, 300-dim vectors).
- Uses batch_size=10 for faster processing with minimal memory usage.
- Stores embeddings in ChromaDB per batch to minimize memory footprint.
- Reuses existing collections if standards files are unchanged (via file hashes).
- Loads and validates requirements CSV (66 criteria, 3 columns: category, criterion, description).
"""

# Initialize logger
logger = logging.setup_logger(__name__)

class DatabaseBuilder:
    def __init__(self, standards_files=None, requirements_file=None):
        """
        Initialize the database builder with configuration and SpaCy model.
        
        Args:
            standards_files (list, optional): List of standards files (e.g., ['ifrs_s1.pdf']).
            requirements_file (str, optional): Requirements file (e.g., 'UNCTAD_requirements.csv').
        """
        self.config = Config(standards_file=standards_files[0] if standards_files else None, 
                           requirements_file=requirements_file)
        
        self.standards_files = standards_files or [self.config.standards_file] if self.config.standards_file else self.config.available_standards
        if not self.standards_files:
            logger.error("No standards files available")
            raise ValueError("No standards files available")
        
        self.requirements_file = requirements_file or self.config.requirements_file
        self.standards_paths = [os.path.join(self.config.standards_dir, f) for f in self.standards_files]
        self.requirements_path = os.path.join(self.config.requirements_dir, self.requirements_file)
        
        self.chroma_client = chromadb.PersistentClient(
            path=os.path.join(self.config.project_root, 'chromadb')
        )
        
        try:
            self.embedding_model = spacy.load('en_core_web_sm')
            logger.info("Loaded SpaCy en_core_web_sm model for embeddings (~12 MB)")
        except Exception as e:
            logger.error(f"Failed to load SpaCy model: {str(e)}")
            raise
        
        self.cache_dir = os.path.join(self.config.project_root, 'chromadb', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.requirements_cache_file = os.path.join(self.cache_dir, 'requirements_cache.pkl')
        
        logger.info(f"Initialized DatabaseBuilder with standards: {self.standards_files}, requirements: {self.requirements_file}")
    
    def get_file_hash(self, file_path):
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path (str): Path to the file.
        
        Returns:
            str: SHA256 hash of the file.
        """
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            file_hash = sha256.hexdigest()
            logger.info(f"Calculated hash for {file_path}: {file_hash}")
            return file_hash
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            raise
    
    def split_standards_pdf(self, pdf_path, criteria_mapping):
        """
        Split a standards PDF into paragraphs with metadata.
        
        Args:
            pdf_path (str): Path to the standards PDF.
            criteria_mapping (dict): Mapping of criteria to standard codes.
        
        Returns:
            list: List of dictionaries with paragraph text, metadata, and ID.
        """
        try:
            file_utils.validate_path(pdf_path)
            paragraphs = []
            framework = os.path.splitext(os.path.basename(pdf_path))[0].replace('ESG_Framework_', '')
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if not text:
                        logger.warning(f"No text extracted from page {page_num} in {pdf_path}")
                        continue
                    
                    para_texts = re.split(r'\n{2,}|\s{4,}', text.strip())
                    for para_idx, paragraph in enumerate(para_texts):
                        paragraph = paragraph.strip()
                        if len(paragraph) < 30 or not re.search(r'[a-zA-Z0-9]', paragraph):
                            logger.info(f"Skipping paragraph {para_idx} on page {page_num} in {pdf_path}: too short or no alphanumeric content")
                            continue
                        
                        metadata = self._extract_metadata(paragraph, page_num, framework, criteria_mapping)
                        paragraph_id = f"{os.path.basename(pdf_path)}_page{page_num}_para{para_idx}"
                        paragraphs.append({
                            'text': paragraph,
                            'metadata': metadata,
                            'id': paragraph_id
                        })
                        logger.info(f"Extracted paragraph {para_idx} from page {page_num} in {pdf_path}")
            
            logger.info(f"Split {pdf_path} into {len(paragraphs)} paragraphs")
            return paragraphs
        
        except Exception as e:
            logger.error(f"Error splitting standards PDF {pdf_path}: {str(e)}")
            raise
    
    def _extract_metadata(self, paragraph, page_num, framework, criteria_mapping):
        """
        Extract metadata from a paragraph.
        
        Args:
            paragraph (str): Paragraph text.
            page_num (int): Page number.
            framework (str): Framework name (e.g., 'ifrs_s1').
            criteria_mapping (dict): Mapping of criteria to standard codes.
        
        Returns:
            dict: Metadata with framework, code, topic, page, and criteria.
        """
        metadata = {
            'framework': framework,
            'code': '',
            'topic': '',
            'page': str(page_num),
            'criteria': ''
        }
        
        code_match = re.search(r'\b[S]?\d{1,3}-\d{1,2}\b', paragraph)
        if code_match:
            metadata['code'] = code_match.group(0)
        
        text_lower = paragraph.lower()
        if 'emission' in text_lower or 'carbon' in text_lower:
            metadata['topic'] = 'emissions'
        elif 'diversity' in text_lower or 'inclusion' in text_lower:
            metadata['topic'] = 'diversity'
        elif 'governance' in text_lower or 'board' in text_lower:
            metadata['topic'] = 'governance'
        elif 'jobs' in text_lower or 'employment' in text_lower:
            metadata['topic'] = 'jobs'
        else:
            metadata['topic'] = 'general'
        
        criteria_list = []
        paragraph_lower = paragraph.lower()
        for criterion, details in criteria_mapping.items():
            criterion_text = f"{criterion} {details['description']}".lower()
            if metadata['code'] and metadata['code'] in criterion_text:
                criteria_list.append(criterion)
            elif any(keyword in criterion_text for keyword in paragraph_lower.split() if len(keyword) > 3):
                criteria_list.append(criterion)
        
        metadata['criteria'] = ','.join(criteria_list) if criteria_list else ''
        
        return metadata
    
    def embed_sections(self, sections, collection_name):
        """
        Embed paragraphs using SpaCy en_core_web_sm and store in ChromaDB.
        
        Args:
            sections (list): List of paragraph dictionaries with text, metadata, and ID.
            collection_name (str): Name of the ChromaDB collection.
        
        Returns:
            chromadb.Collection: ChromaDB collection with embedded paragraphs.
        """
        try:
            collection = self.chroma_client.get_or_create_collection(name=collection_name)
            
            texts = [section['text'] for section in sections]
            ids = [section['id'] for section in sections]
            metadatas = [section['metadata'] for section in sections]
            
            for metadata in metadatas:
                for key, value in metadata.items():
                    if not isinstance(value, (str, int, float, bool)) and value is not None:
                        logger.error(f"Invalid metadata value for {key}: {value} (type: {type(value).__name__})")
                        raise ValueError(f"Metadata value for {key} must be str, int, float, bool, or None")
            
            if not texts:
                logger.warning(f"No valid sections to embed for {collection_name}")
                return collection
            
            batch_size = 10
            logger.info(f"Embedding {len(texts)} paragraphs in batches of {batch_size}")
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                if not batch_texts:
                    logger.debug(f"Skipping empty batch at index {i}")
                    continue
                
                batch_ids = ids[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                batch_embeddings = []
                logger.info(f"Processing batch {i//batch_size + 1}/{len(texts)//batch_size + 1} ({len(batch_texts)} paragraphs)")
                
                for idx, text in enumerate(batch_texts):
                    try:
                        if not re.search(r'[a-zA-Z0-9]', text):
                            logger.info(f"Skipping paragraph {i + idx} in batch {i//batch_size + 1}: no alphanumeric content")
                            batch_embeddings.append(np.zeros(300).tolist())
                            continue
                        doc = self.embedding_model(text)
                        embedding = doc.vector.tolist()
                        batch_embeddings.append(embedding)
                        logger.info(f"Embedded paragraph {i + idx} in batch {i//batch_size + 1} (length: {len(text)} chars)")
                        if (i + idx) % 10 == 0:
                            memory = psutil.virtual_memory()
                            logger.info(f"Memory usage after paragraph {i + idx}: {memory.percent}% used, {memory.available / 1024**3:.2f} GB free")
                        del doc
                        gc.collect()
                    except Exception as e:
                        logger.error(f"Error embedding paragraph {i + idx} in batch {i//batch_size + 1}: {str(e)}")
                        batch_embeddings.append(np.zeros(300).tolist())
                
                try:
                    valid_indices = [j for j, emb in enumerate(batch_embeddings) if not np.all(np.array(emb) == 0)]
                    if valid_indices:
                        valid_texts = [batch_texts[j] for j in valid_indices]
                        valid_ids = [batch_ids[j] for j in valid_indices]
                        valid_metadatas = [batch_metadatas[j] for j in valid_indices]
                        valid_embeddings = [batch_embeddings[j] for j in valid_indices]
                        
                        collection.add(
                            documents=valid_texts,
                            embeddings=valid_embeddings,
                            metadatas=valid_metadatas,
                            ids=valid_ids
                        )
                        logger.info(f"Stored {len(valid_texts)} paragraphs in ChromaDB for batch {i//batch_size + 1}")
                    else:
                        logger.warning(f"No valid embeddings for batch {i//batch_size + 1}")
                except Exception as e:
                    logger.error(f"Error storing batch {i//batch_size + 1} in ChromaDB: {str(e)}")
                    raise
                
                del batch_texts, batch_ids, batch_metadatas, batch_embeddings
                gc.collect()
            
            logger.info(f"Successfully stored all paragraphs in ChromaDB collection: {collection_name}")
            return collection
        
        except Exception as e:
            logger.error(f"Error embedding paragraphs for {collection_name}: {str(e)}")
            raise
    
    def check_existing_collection(self, pdf_path, collection_name):
        """
        Check if a ChromaDB collection exists and matches the PDF's hash.
        
        Args:
            pdf_path (str): Path to the standards PDF.
            collection_name (str): Name of the ChromaDB collection.
        
        Returns:
            bool: True if collection exists and hash matches, False otherwise.
        """
        try:
            collections = self.chroma_client.list_collections()
            if not any(c.name == collection_name for c in collections):
                logger.info(f"No existing collection found for {collection_name}")
                return False
            
            cache_file = os.path.join(self.cache_dir, f"{collection_name}_hash.pkl")
            current_hash = self.get_file_hash(pdf_path)
            
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    cached_hash = pickle.load(f)
                if cached_hash == current_hash:
                    logger.info(f"Existing collection {collection_name} matches file hash")
                    return True
            
            logger.info(f"Collection {collection_name} exists but file has changed")
            return False
        
        except Exception as e:
            logger.error(f"Error checking collection {collection_name}: {str(e)}")
            return False
    
    def cache_file_hash(self, pdf_path, collection_name):
        """
        Cache the file hash for a standards PDF.
        
        Args:
            pdf_path (str): Path to the standards PDF.
            collection_name (str): Name of the ChromaDB collection.
        """
        try:
            file_hash = self.get_file_hash(pdf_path)
            cache_file = os.path.join(self.cache_dir, f"{collection_name}_hash.pkl")
            with open(cache_file, 'wb') as f:
                pickle.dump(file_hash, f)
            logger.info(f"Cached file hash for {pdf_path}")
        except Exception as e:
            logger.error(f"Error caching hash for {pdf_path}: {str(e)}")
            raise
    
    def validate_requirements_csv(self):
        """
        Load and validate the requirements CSV, using cache if unchanged.
        
        Returns:
            pd.DataFrame: Validated requirements DataFrame.
        """
        try:
            file_utils.validate_path(self.requirements_path)
            current_hash = self.get_file_hash(self.requirements_path)
            
            if os.path.exists(self.requirements_cache_file):
                with open(self.requirements_cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                if cached_data['hash'] == current_hash:
                    logger.info(f"Using cached requirements validation for {self.requirements_path}")
                    return pd.DataFrame(cached_data['data'])
            
            df = pd.read_csv(self.requirements_path)
            
            if len(df) != 66:
                logger.error(f"Requirements CSV {self.requirements_path} has {len(df)} rows, expected 66")
                raise ValueError("Requirements CSV must have exactly 66 rows")
            
            expected_columns = ['category', 'criterion', 'description']
            if not all(col in df.columns for col in expected_columns):
                missing = [col for col in expected_columns if col not in df.columns]
                logger.error(f"Missing columns in requirements CSV: {missing}")
                raise ValueError(f"Missing columns in requirements CSV: {missing}")
            
            cache_data = {'hash': current_hash, 'data': df.to_dict()}
            with open(self.requirements_cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            logger.info(f"Validated and cached requirements CSV: {self.requirements_path} with 66 criteria")
            
            return df
        
        except Exception as e:
            logger.error(f"Error validating requirements CSV {self.requirements_path}: {str(e)}")
            raise
    
    def build_criteria_mapping(self, requirements_df):
        """
        Build a mapping of criteria to standard codes or keywords for metadata extraction.
        
        Args:
            requirements_df (pd.DataFrame): Requirements DataFrame with category, criterion, description.
        
        Returns:
            dict: Mapping of criterion to description.
        """
        try:
            criteria_mapping = {}
            for _, row in requirements_df.iterrows():
                criterion = row['criterion']
                description = row['description']
                criteria_mapping[criterion] = {'description': description}
            logger.info(f"Built criteria mapping for {len(criteria_mapping)} criteria")
            return criteria_mapping
        except Exception as e:
            logger.error(f"Error building criteria mapping: {str(e)}")
            raise
    
    def initialize_database(self):
        """
        Initialize ChromaDB with all selected standards and validate requirements.
        
        Returns:
            tuple: (dict of ChromaDB collections, requirements DataFrame).
        """
        try:
            requirements_df = self.validate_requirements_csv()
            criteria_mapping = self.build_criteria_mapping(requirements_df)
            
            collections = {}
            for pdf_path in self.standards_paths:
                collection_name = f"esg_standards_{os.path.splitext(os.path.basename(pdf_path))[0]}"
                
                if self.check_existing_collection(pdf_path, collection_name):
                    collections[os.path.basename(pdf_path)] = self.chroma_client.get_collection(collection_name)
                    logger.info(f"Reused existing collection for {pdf_path}")
                    continue
                
                sections = self.split_standards_pdf(pdf_path, criteria_mapping)
                if not sections:
                    logger.warning(f"No paragraphs extracted from {pdf_path}")
                    continue
                
                collection = self.embed_sections(sections, collection_name)
                collections[os.path.basename(pdf_path)] = collection
                
                self.cache_file_hash(pdf_path, collection_name)
                logger.info(f"Processed standards file: {pdf_path}")
            
            if not collections:
                logger.error("No standards files successfully processed")
                raise ValueError("No standards files successfully processed")
            
            logger.info("Database initialization completed successfully")
            return collections, requirements_df
        
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize ESG Compliance Verification System database")
    parser.add_argument('--standards', nargs='+', help="List of standards files (e.g., ifrs_s1.pdf)")
    parser.add_argument('--requirements', help="Requirements file (e.g., UNCTAD_requirements.csv)")
    args = parser.parse_args()
    
    builder = DatabaseBuilder(standards_files=args.standards, requirements_file=args.requirements)
    collections, requirements_df = builder.initialize_database()
    for file_name, collection in collections.items():
        logger.info(f"Initialized ChromaDB collection for {file_name} with {collection.count()} paragraphs")
    logger.info(f"Loaded requirements with {len(requirements_df)} criteria")
