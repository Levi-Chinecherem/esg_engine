import os
import glob
from utils import logging

"""
File: esg_system/utils/file_utils.py
Role: Utility for file operations and dynamic file selection.
Key Functionality:
- Validates file and directory paths.
- Lists available standards and requirements files.
- Reads and writes files with error handling.
- Supports dynamic selection of files based on user input or configuration.
"""

# Initialize logger
logger = logging.setup_logger(__name__)

def validate_path(path):
    """
    Validate if a file or directory exists.
    
    Args:
        path (str): Path to validate.
    
    Returns:
        bool: True if path exists, False otherwise.
    A
    Raises:
        FileNotFoundError: If path does not exist.
    """
    try:
        if not os.path.exists(path):
            logger.error(f"Path not found: {path}")
            raise FileNotFoundError(f"Path not found: {path}")
        logger.info(f"Validated path: {path}")
        return True
    except Exception as e:
        logger.error(f"Path validation failed: {str(e)}")
        raise

def list_standards_files(standards_dir):
    """
    List all PDF files in the standards directory.
    
    Args:
        standards_dir (str): Path to standards directory.
    
    Returns:
        list: List of PDF file names.
    """
    try:
        validate_path(standards_dir)
        pdf_files = glob.glob(os.path.join(standards_dir, "*.pdf"))
        files = [os.path.basename(f) for f in pdf_files]
        logger.info(f"Found standards files: {files}")
        return files
    except Exception as e:
        logger.error(f"Error listing standards files: {str(e)}")
        return []

def list_requirements_files(requirements_dir):
    """
    List all CSV files in the requirements directory.
    
    Args:
        requirements_dir (str): Path to requirements directory.
    
    Returns:
        list: List of CSV file names.
    """
    try:
        validate_path(requirements_dir)
        csv_files = glob.glob(os.path.join(requirements_dir, "*.csv"))
        files = [os.path.basename(f) for f in csv_files]
        logger.info(f"Found requirements files: {files}")
        return files
    except Exception as e:
        logger.error(f"Error listing requirements files: {str(e)}")
        return []

def read_file(file_path):
    """
    Read content from a file.
    
    Args:
        file_path (str): Path to the file.
    
    Returns:
        str: File content.
    
    Raises:
        FileNotFoundError: If file does not exist.
        IOError: If file reading fails.
    """
    try:
        validate_path(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Read file: {file_path}")
        return content
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise

def write_file(file_path, content):
    """
    Write content to a file.
    
    Args:
        file_path (str): Path to the file.
        content (str): Content to write.
    
    Raises:
        IOError: If file writing fails.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Wrote file: {file_path}")
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {str(e)}")
        raise