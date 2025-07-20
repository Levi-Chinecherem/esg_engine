import json
import pandas as pd
from llama_cpp import Llama
from utils import logging, file_utils
from utils.pdf_extraction import extract_pdf_with_fallback
from config import Config

"""
File: data_extraction/supplementary_extract.py
Role: Extracts supplementary data (company profile, stakeholder engagement, case studies, chart data) from a sustainability report using Mistral-7B for the ESG Compliance Verification System.
Key Functionality:
- Extracts company profile (about, mission, vision, core values).
- Extracts stakeholder engagement (survey satisfaction, forums, meetings, themes).
- Extracts case studies (title, description, impact).
- Extracts chart data (emissions, diversity, benchmarking, progress).
- Dynamically loads categories from requirements CSV for benchmarking.
- Uses Mistral-7B (mistral-7b-instruct-v0.1.Q4_K_M.gguf) with optimized prompts.
- Re-reads the report PDF for comprehensive extraction.
- Logs extraction steps and errors for traceability.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

def initialize_model():
    """
    Initialize the Mistral model for data extraction.
    
    Returns:
        Llama: Initialized Mistral model.
    
    Raises:
        FileNotFoundError: If model file is missing.
        RuntimeError: If model initialization fails.
    """
    try:
        config = Config()
        model_path = config.get_model_path()
        file_utils.validate_path(model_path)
        model = Llama(model_path=model_path, n_ctx=2048, n_gpu_layers=1)
        logger.info("Mistral model initialized successfully")
        return model
    except Exception as e:
        logger.error(f"Model initialization failed: {str(e)}")
        raise

def extract_supplementary_data(report_path, requirements_csv):
    """
    Extract supplementary data from the sustainability report for the PDF report.
    
    Args:
        report_path (str): Path to the company report PDF.
        requirements_csv (str): Path to the requirements CSV file (e.g., UNCTAD_requirements.csv).
    
    Returns:
        dict: Extracted supplementary data.
            Example: {
                'company_profile': {'about': '...', 'mission': '...', 'vision': '...', 'core_values': [...]},
                'stakeholder_engagement': {'survey_satisfaction': '...', 'forums': '...', 'meetings': '...', 'themes': [...]},
                'case_studies': [{'title': '...', 'description': '...', 'impact': '...'}, ...],
                'emissions_data': [{'year': '...', 'scope1': ..., 'scope2': ...}, ...],
                'diversity_data': [{'category': '...', 'year1': ..., 'year2': ...}, ...],
                'benchmarking_data': [{'category': '...', 'company': ..., 'industry': ...}, ...],
                'progress_data': [{'quarter': '...', 'progress': ...}, ...]
            }
    
    Raises:
        FileNotFoundError: If report_path or requirements_csv is invalid.
        Exception: For extraction errors.
    """
    try:
        file_utils.validate_path(report_path)
        file_utils.validate_path(requirements_csv)
        model = initialize_model()
        extracted_data = extract_pdf_with_fallback(report_path)
        full_text = ' '.join([page['text'] for page in extracted_data if page['text']])[:1500]  # Limit to avoid token overflow
        
        # Load categories from requirements CSV
        requirements_df = pd.read_csv(requirements_csv)
        if requirements_df.empty or not all(col in requirements_df.columns for col in ['category', 'criterion', 'description']):
            logger.error(f"Invalid requirements CSV format: {requirements_csv}")
            raise ValueError("Requirements CSV must have columns: category, criterion, description")
        categories = requirements_df['category'].unique().tolist()
        logger.info(f"Loaded categories for benchmarking: {categories}")
        
        supplementary_data = {
            'company_profile': {'about': 'N/A', 'mission': 'N/A', 'vision': 'N/A', 'core_values': []},
            'stakeholder_engagement': {'survey_satisfaction': 'N/A', 'forums': 'N/A', 'meetings': 'N/A', 'themes': []},
            'case_studies': [],
            'emissions_data': [],
            'diversity_data': [],
            'benchmarking_data': [],
            'progress_data': []
        }
        
        # Company Profile
        profile_prompt = """
        Extract the company profile from the sustainability report, including about, mission, vision, and core values. If not explicitly stated, infer from context (e.g., company overview, goals, or values sections). Return 'N/A' for missing fields and an empty list for core_values if none found.

        **Text**:
        {text}

        **Output Format**:
        ```json
        {
            "about": "<description>",
            "mission": "<mission statement>",
            "vision": "<vision statement>",
            "core_values": ["<value1>", "<value2>", ...]
        }
        ```
        """
        response = model(profile_prompt.format(text=full_text), max_tokens=300, temperature=0.2)
        try:
            supplementary_data['company_profile'] = json.loads(response['choices'][0]['text'].strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse company profile: {str(e)}")
        
        # Stakeholder Engagement
        engagement_prompt = """
        Extract stakeholder engagement metrics from the report, including survey satisfaction, community forums, investor meetings, and feedback themes. Infer from relevant sections (e.g., stakeholder, community, or investor relations). Return 'N/A' for missing metrics and an empty list for themes if none found.

        **Text**:
        {text}

        **Output Format**:
        ```json
        {
            "survey_satisfaction": "<percentage or description>",
            "forums": "<number or description>",
            "meetings": "<number or description>",
            "themes": ["<theme1>", "<theme2>", ...]
        }
        ```
        """
        response = model(engagement_prompt.format(text=full_text), max_tokens=200, temperature=0.2)
        try:
            supplementary_data['stakeholder_engagement'] = json.loads(response['choices'][0]['text'].strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse stakeholder engagement: {str(e)}")
        
        # Case Studies
        case_study_prompt = """
        Extract up to two case studies from the report, each with a title, description, and impact. Infer from initiatives, projects, or success stories if not explicitly labeled. Return an empty list if none found.

        **Text**:
        {text}

        **Output Format**:
        ```json
        [
            {"title": "<title>", "description": "<description>", "impact": "<impact>"},
            {"title": "<title>", "description": "<description>", "impact": "<impact>"}
        ]
        ```
        """
        response = model(case_study_prompt.format(text=full_text), max_tokens=400, temperature=0.2)
        try:
            supplementary_data['case_studies'] = json.loads(response['choices'][0]['text'].strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse case studies: {str(e)}")
        
        # Emissions Data (Historical Trends)
        emissions_prompt = """
        Extract historical emissions data (Scope 1 and Scope 2) for the last three years from the report. Infer years if not explicit (e.g., assume 2022-2024 for a 2025 report). Return an empty list if none found.

        **Text**:
        {text}

        **Output Format**:
        ```json
        [
            {"year": "<year>", "scope1": "<value>", "scope2": "<value>"},
            ...
        ]
        ```
        """
        response = model(emissions_prompt.format(text=full_text), max_tokens=200, temperature=0.2)
        try:
            supplementary_data['emissions_data'] = json.loads(response['choices'][0]['text'].strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse emissions data: {str(e)}")
        
        # Diversity Data
        diversity_prompt = """
        Extract diversity data (Gender, Ethnic, Leadership) for the last two years from the report. Infer years if not explicit (e.g., 2023-2024 for a 2025 report). Return an empty list if none found.

        **Text**:
        {text}

        **Output Format**:
        ```json
        [
            {"category": "Gender", "<year1>": "<value>", "<year2>": "<value>"},
            {"category": "Ethnic", "<year1>": "<value>", "<year2>": "<value>"},
            {"category": "Leadership", "<year1>": "<value>", "<year2>": "<value>"}
        ]
        ```
        """
        response = model(diversity_prompt.format(text=full_text), max_tokens=200, temperature=0.2)
        try:
            supplementary_data['diversity_data'] = json.loads(response['choices'][0]['text'].strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse diversity data: {str(e)}")
        
        # Benchmarking Data
        benchmarking_prompt = """
        Extract or infer ESG compliance scores for {categories} compared to industry averages from the report. If not explicit, estimate industry averages based on context. Return an empty list if none found.

        **Text**:
        {text}

        **Output Format**:
        ```json
        [
            {{"category": "{category1}", "company": "<value>", "industry": "<value>"}},
            {{"category": "{category2}", "company": "<value>", "industry": "<value>"}},
            ...
        ]
        ```
        """
        # Dynamically insert categories
        category_str = ', '.join(categories)
        formatted_prompt = benchmarking_prompt.format(categories=category_str, text=full_text, category1=categories[0], category2=categories[1] if len(categories) > 1 else categories[0])
        response = model(formatted_prompt, max_tokens=200, temperature=0.2)
        try:
            supplementary_data['benchmarking_data'] = json.loads(response['choices'][0]['text'].strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse benchmarking data: {str(e)}")
        
        # Progress Data
        progress_prompt = """
        Extract or infer progress toward ESG goals for the next three quarters (e.g., Q2 2025, Q3 2025, Q4 2025) from the report. Return an empty list if none found.

        **Text**:
        {text}

        **Output Format**:
        ```json
        [
            {"quarter": "Q2 2025", "progress": "<value>"},
            {"quarter": "Q3 2025", "progress": "<value>"},
            {"quarter": "Q4 2025", "progress": "<value>"}
        ]
        ```
        """
        response = model(progress_prompt.format(text=full_text), max_tokens=200, temperature=0.2)
        try:
            supplementary_data['progress_data'] = json.loads(response['choices'][0]['text'].strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse progress data: {str(e)}")
        
        logger.info("Extracted supplementary data for report")
        return supplementary_data
    
    except Exception as e:
        logger.error(f"Supplementary data extraction failed: {str(e)}")
        raise