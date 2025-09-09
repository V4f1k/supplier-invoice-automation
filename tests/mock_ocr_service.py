"""Mock OCR service for testing"""

from typing import Union
from pathlib import Path
from loguru import logger


async def extract_text(file_path: Union[str, Path]) -> str:
    """
    Mock function to extract text from a file for testing
    
    Args:
        file_path: Path to the file to process
        
    Returns:
        Mock extracted text based on file extension
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Return mock text based on file extension
    if file_path.suffix.lower() == '.pdf':
        return f"Mock text extracted from PDF: {file_path.name}"
    elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
        return f"Mock text extracted from image: {file_path.name}"
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")