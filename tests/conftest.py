"""Test configuration and fixtures"""

import pytest
from unittest.mock import patch, Mock
import os

# Set test environment variables before importing app
os.environ["GOOGLE_API_KEY"] = "test-api-key"

# Mock google generative AI to prevent actual API calls during tests
mock_genai = Mock()
mock_model = Mock()
mock_model.generate_content = Mock(return_value=Mock(text='{"test": "data"}'))
mock_genai.GenerativeModel.return_value = mock_model

with patch.dict('sys.modules', {'google.generativeai': mock_genai}):
    pass