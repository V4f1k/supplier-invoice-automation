"""Tests for utility functions"""

import hashlib
import pytest

from app.utils import calculate_file_hash


class TestUtils:
    """Test cases for utility functions"""
    
    def test_calculate_file_hash_simple(self):
        """Test hash calculation with simple content"""
        # Setup
        content = b"Hello, World!"
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Execute
        result = calculate_file_hash(content)
        
        # Assert
        assert result == expected_hash
        assert len(result) == 64  # SHA-256 produces 64 character hex string
    
    def test_calculate_file_hash_empty_file(self):
        """Test hash calculation with empty file"""
        # Setup
        content = b""
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Execute
        result = calculate_file_hash(content)
        
        # Assert
        assert result == expected_hash
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    def test_calculate_file_hash_binary_content(self):
        """Test hash calculation with binary content"""
        # Setup - simulate PDF/image binary content
        content = bytes([0x25, 0x50, 0x44, 0x46, 0x2D, 0x31, 0x2E, 0x34])  # %PDF-1.4
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Execute
        result = calculate_file_hash(content)
        
        # Assert
        assert result == expected_hash
        assert len(result) == 64
    
    def test_calculate_file_hash_large_content(self):
        """Test hash calculation with large content"""
        # Setup - 1MB of data
        content = b"A" * (1024 * 1024)
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Execute
        result = calculate_file_hash(content)
        
        # Assert
        assert result == expected_hash
        assert len(result) == 64
    
    def test_calculate_file_hash_consistency(self):
        """Test that same content produces same hash"""
        # Setup
        content = b"Test content for consistency"
        
        # Execute
        hash1 = calculate_file_hash(content)
        hash2 = calculate_file_hash(content)
        
        # Assert
        assert hash1 == hash2
    
    def test_calculate_file_hash_different_content(self):
        """Test that different content produces different hashes"""
        # Setup
        content1 = b"First content"
        content2 = b"Second content"
        
        # Execute
        hash1 = calculate_file_hash(content1)
        hash2 = calculate_file_hash(content2)
        
        # Assert
        assert hash1 != hash2
        assert len(hash1) == 64
        assert len(hash2) == 64
    
    def test_calculate_file_hash_special_characters(self):
        """Test hash calculation with special characters and unicode"""
        # Setup
        content = "Special characters: äöü ñ 中文 🚀".encode('utf-8')
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Execute
        result = calculate_file_hash(content)
        
        # Assert
        assert result == expected_hash
        assert len(result) == 64
    
    def test_calculate_file_hash_none_input(self):
        """Test error handling for None input"""
        with pytest.raises(ValueError, match="file_content cannot be None"):
            calculate_file_hash(None)
    
    def test_calculate_file_hash_invalid_type(self):
        """Test error handling for invalid input type"""
        with pytest.raises(ValueError, match="file_content must be bytes"):
            calculate_file_hash("not bytes")
        
        with pytest.raises(ValueError, match="file_content must be bytes"):
            calculate_file_hash(123)