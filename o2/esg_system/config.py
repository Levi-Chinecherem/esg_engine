import os
from utils import config_loader, logging, file_utils

"""
File: config.py
Role: Centralized configuration management for the ESG Compliance Verification System.
Key Functionality:
- Loads and validates paths for directories (input, standards, requirements, output, templates, logs).
- Lists available standards and requirements files for dynamic selection.
- Supports selection of specific standards and requirements files via CLI or .env.
- Validates all paths and files at startup.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

class Config:
    """Manages configuration settings for the ESG system."""
    
    def __init__(self, standards_file=None, requirements_file=None):
        """
        Initialize configuration with paths.
        
        Args:
            standards_file (str, optional): Specific standards file (e.g., 'ifrs_s1.pdf'). If None, uses .env or lists available files.
            requirements_file (str, optional): Specific requirements file (e.g., 'UNCTAD_requirements.csv'). If None, uses .env or lists available files.
        """
        # Load configuration from .env or environment variables
        self.config = config_loader.load_config()
        
        # Set project root and directory paths (relative to esg_system)
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.input_dir = os.path.join(self.project_root, 'input')
        self.standards_dir = os.path.join(self.project_root, 'standards')
        self.requirements_dir = os.path.join(self.project_root, 'requirements')
        self.output_dir = os.path.join(self.project_root, 'output')
        self.templates_dir = os.path.join(self.project_root, 'templates')
        self.logs_dir = os.path.join(self.project_root, 'logs')
        self.db_path = os.path.join(self.project_root, 'chromadb')
        
        # Get available standards and requirements files
        self.available_standards = file_utils.list_standards_files(self.standards_dir)
        self.available_requirements = file_utils.list_requirements_files(self.requirements_dir)
        
        # Select standards file: CLI > .env > first available file
        self.standards_file = standards_file or self.config.get('STANDARDS_FILE', 
                            self.available_standards[0] if self.available_standards else None)
        if not self.standards_file:
            logger.error("No standards file specified and none found in standards directory")
            raise ValueError("No standards file available")
        
        # Select requirements file: CLI > .env > first available file
        self.requirements_file = requirements_file or self.config.get('REQUIREMENTS_FILE', 
                                self.available_requirements[0] if self.available_requirements else None)
        if not self.requirements_file:
            logger.error("No requirements file specified and none found in requirements directory")
            raise ValueError("No requirements file available")
        
        # Tesseract path
        self.tesseract_cmd = self.config.get('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        
        # Validate all paths
        self._validate_paths()
    
    def _validate_paths(self):
        """
        Validate all configured paths and files.
        
        Raises:
            FileNotFoundError: If a required directory or file is missing.
            ValueError: If no valid standards or requirements files are found.
        """
        try:
            # Validate directories
            for dir_path in [self.input_dir, self.standards_dir, self.requirements_dir, 
                           self.output_dir, self.templates_dir, self.logs_dir, self.db_path]:
                if not os.path.exists(dir_path):
                    logger.error(f"Directory not found: {dir_path}")
                    raise FileNotFoundError(f"Directory not found: {dir_path}")
                logger.info(f"Validated directory: {dir_path}")
            
            # Validate standards file
            standards_path = os.path.join(self.standards_dir, self.standards_file)
            if not os.path.isfile(standards_path):
                logger.error(f"Standards file not found: {standards_path}")
                raise FileNotFoundError(f"Standards file not found: {standards_path}")
            logger.info(f"Validated standards file: {standards_path}")
            
            # Validate requirements file
            requirements_path = os.path.join(self.requirements_dir, self.requirements_file)
            if not os.path.isfile(requirements_path):
                logger.error(f"Requirements file not found: {requirements_path}")
                raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
            logger.info(f"Validated requirements file: {requirements_path}")
            
            # Validate Tesseract
            if not os.path.isfile(self.tesseract_cmd):
                logger.error(f"Tesseract executable not found: {self.tesseract_cmd}")
                raise FileNotFoundError(f"Tesseract executable not found: {self.tesseract_cmd}")
            logger.info(f"Validated Tesseract: {self.tesseract_cmd}")
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise
    
    def get_config(self):
        """
        Get the configuration dictionary.
        
        Returns:
            dict: Configuration settings with paths and files.
        """
        return {
            'project_root': self.project_root,
            'input_dir': self.input_dir,
            'standards_dir': self.standards_dir,
            'requirements_dir': self.requirements_dir,
            'output_dir': self.output_dir,
            'templates_dir': self.templates_dir,
            'logs_dir': self.logs_dir,
            'db_path': self.db_path,
            'standards_file': self.standards_file,
            'available_standards': self.available_standards,
            'requirements_file': self.requirements_file,
            'available_requirements': self.available_requirements,
            'tesseract_cmd': self.tesseract_cmd
        }
