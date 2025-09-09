"""Utility functions"""

import hashlib
from typing import Union


def calculate_file_hash(file_content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content with validation
    
    Args:
        file_content: Raw bytes content of the file
        
    Returns:
        SHA-256 hash as hexadecimal string
        
    Raises:
        ValueError: If file_content is not bytes or is None
    """
    if file_content is None:
        raise ValueError("file_content cannot be None")
    if not isinstance(file_content, bytes):
        raise ValueError("file_content must be bytes")
    
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_content)
    return sha256_hash.hexdigest()