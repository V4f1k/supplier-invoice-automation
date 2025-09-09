"""Tests for service modules"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from app.services.ocr_service import OCRService, extract_text, get_ocr_service


class TestOCRService:
    """Test cases for OCR service"""
    
    @pytest.fixture
    def mock_ocr_model(self):
        """Mock Surya OCR model"""
        mock_model = MagicMock()
        mock_model.extract_text.return_value = [
            [
                MagicMock(text="Sample extracted text"),
                MagicMock(text="Another line of text")
            ]
        ]
        return mock_model
    
    @pytest.fixture
    def mock_image(self):
        """Mock PIL Image"""
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_img.convert.return_value = mock_img
        return mock_img
    
    @pytest.mark.asyncio
    @patch('app.services.ocr_service.OCRModel')
    @patch('app.services.ocr_service.Image')
    async def test_extract_from_image_success(self, mock_image_class, mock_ocr_model_class):
        """Test successful text extraction from image"""
        # Setup mocks
        mock_model = MagicMock()
        mock_model.extract_text.return_value = [
            [
                MagicMock(text="Invoice #12345"),
                MagicMock(text="Amount: $100.00")
            ]
        ]
        mock_ocr_model_class.return_value = mock_model
        
        mock_image = MagicMock()
        mock_image.mode = "RGB"
        mock_image_class.open.return_value = mock_image
        
        # Create a temporary test image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(b"fake image data")
            temp_path = temp_file.name
        
        try:
            # Create service and test
            service = OCRService()
            result = await service.extract_text(temp_path)
            
            # Assertions
            assert "Invoice #12345" in result
            assert "Amount: $100.00" in result
            mock_image_class.open.assert_called_once_with(Path(temp_path))
            mock_model.extract_text.assert_called_once()
            
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @pytest.mark.asyncio
    @patch('app.services.ocr_service.OCRModel')
    async def test_extract_text_unsupported_format(self, mock_ocr_model_class):
        """Test error handling for unsupported file formats"""
        from app.exceptions import FileProcessingError
        
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"plain text file")
            temp_path = temp_file.name
        
        try:
            service = OCRService()
            
            with pytest.raises(FileProcessingError, match="Unsupported file format"):
                await service.extract_text(temp_path)
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @pytest.mark.asyncio
    @patch('app.services.ocr_service.OCRModel')
    async def test_extract_text_file_not_found(self, mock_ocr_model_class):
        """Test error handling when file doesn't exist"""
        from app.exceptions import FileProcessingError
        
        service = OCRService()
        non_existent_path = "/path/to/nonexistent/file.png"
        
        with pytest.raises(FileProcessingError, match="File not found"):
            await service.extract_text(non_existent_path)
    
    @pytest.mark.asyncio
    @patch('app.services.ocr_service.OCRModel')
    @patch('app.services.ocr_service.fitz')
    @patch('app.services.ocr_service.Image')
    async def test_extract_from_pdf_success(self, mock_image_class, mock_fitz, mock_ocr_model_class):
        """Test successful text extraction from PDF"""
        # Setup mocks for PDF processing
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.tobytes.return_value = b"fake png data"
        
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz.open.return_value = mock_doc
        
        # Setup OCR model mock
        mock_model = MagicMock()
        mock_model.extract_text.return_value = [
            [
                MagicMock(text="PDF content line 1"),
                MagicMock(text="PDF content line 2")
            ]
        ]
        mock_ocr_model_class.return_value = mock_model
        
        # Setup image mock
        mock_image = MagicMock()
        mock_image.mode = "RGB"
        mock_image_class.open.return_value = mock_image
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"fake pdf data")
            temp_path = temp_file.name
        
        try:
            service = OCRService()
            result = await service.extract_text(temp_path)
            
            # Assertions
            assert "--- Page 1 ---" in result
            assert "PDF content line 1" in result
            assert "PDF content line 2" in result
            mock_fitz.open.assert_called_once_with(Path(temp_path))
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @pytest.mark.asyncio
    @patch('app.services.ocr_service.get_ocr_service')
    async def test_extract_text_convenience_function(self, mock_get_service):
        """Test the convenience extract_text function"""
        mock_service = AsyncMock()
        mock_service.extract_text.return_value = "Extracted text"
        mock_get_service.return_value = mock_service
        
        result = await extract_text("test_file.png")
        
        assert result == "Extracted text"
        mock_service.extract_text.assert_called_once_with("test_file.png")
    
    @pytest.mark.asyncio
    @patch('app.services.ocr_service.OCRModel')
    async def test_get_ocr_service_singleton(self, mock_ocr_model_class):
        """Test that get_ocr_service returns the same instance"""
        # Clear any existing instance
        import app.services.ocr_service
        app.services.ocr_service._ocr_service = None
        
        service1 = await get_ocr_service()
        service2 = await get_ocr_service()
        
        assert service1 is service2  # Same instance
        assert isinstance(service1, OCRService)


class TestAIService:
    """Test cases for AI service"""
    
    @pytest.fixture
    def mock_genai(self):
        """Mock google.generativeai module"""
        import google.generativeai as genai
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"invoice_number": "INV-12345", "vendor_name": "Test Vendor", "total": 100.50, "currency": "USD", "subtotal": 95.00, "tax": 5.50, "items": []}'
        mock_model.generate_content.return_value = mock_response
        
        with patch('app.services.ai_service.genai') as mock_genai_module:
            mock_genai_module.GenerativeModel.return_value = mock_model
            yield mock_genai_module, mock_model, mock_response
    
    @pytest.fixture  
    def mock_settings(self):
        """Mock settings with valid API key"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.google_api_key = "test_api_key"
            yield mock_settings
    
    @pytest.mark.asyncio
    async def test_ai_service_initialization_success(self, mock_settings, mock_genai):
        """Test successful AI service initialization"""
        from app.services.ai_service import AIService
        
        service = AIService()
        
        assert service.model is not None
        assert service.prompt_manager is not None
        assert service.circuit_breaker is not None
        mock_genai[0].configure.assert_called_once_with(api_key="test_api_key")
        
    def test_ai_service_initialization_no_api_key(self):
        """Test AI service initialization fails without API key"""
        from app.services.ai_service import AIService
        from app.exceptions import AiServiceError
        
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.google_api_key = ""
            
            with pytest.raises(AiServiceError, match="Google API key not configured"):
                AIService()
    
    @pytest.mark.asyncio
    async def test_get_structured_data_success(self, mock_settings, mock_genai):
        """Test successful structured data extraction"""
        from app.services.ai_service import AIService
        
        service = AIService()
        
        # Test data
        test_text = "Invoice #INV-12345\nVendor: Test Vendor\nTotal: $100.50"
        
        result = await service.get_structured_data(test_text)
        
        # Assertions
        assert result.invoice_number == "INV-12345"
        assert result.vendor_name == "Test Vendor"
        assert result.total == 100.50
        assert result.currency == "USD"
        assert result.subtotal == 95.00
        assert result.tax == 5.50
        
        # Verify AI was called
        mock_genai[1].generate_content.assert_called_once()
        call_args = mock_genai[1].generate_content.call_args[0][0]
        assert test_text in call_args
        
    @pytest.mark.asyncio
    async def test_get_structured_data_with_table_data(self, mock_settings, mock_genai):
        """Test structured data extraction with table data"""
        from app.services.ai_service import AIService
        
        service = AIService()
        
        test_text = "Invoice #INV-12345"
        table_data = {"tables": ["Item 1 | $10.00", "Item 2 | $20.00"]}
        
        result = await service.get_structured_data(test_text, table_data)
        
        assert result.invoice_number == "INV-12345"
        
        # Verify prompt included table data
        call_args = mock_genai[1].generate_content.call_args[0][0]
        assert test_text in call_args
        assert "Table 1:" in call_args
        assert "Item 1 | $10.00" in call_args
    
    @pytest.mark.asyncio
    async def test_get_structured_data_empty_text(self, mock_settings, mock_genai):
        """Test error handling for empty text input"""
        from app.services.ai_service import AIService
        from app.exceptions import AiServiceError
        
        service = AIService()
        
        with pytest.raises(AiServiceError, match="Empty or invalid invoice text provided"):
            await service.get_structured_data("")
            
        with pytest.raises(AiServiceError, match="Empty or invalid invoice text provided"):
            await service.get_structured_data("   ")
    
    @pytest.mark.asyncio
    async def test_get_structured_data_invalid_json_response(self, mock_settings):
        """Test error handling for invalid JSON response from AI"""
        from app.services.ai_service import AIService
        from app.exceptions import AiServiceError
        
        # Mock AI to return invalid JSON
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON"
        mock_model.generate_content.return_value = mock_response
        
        with patch('app.services.ai_service.genai') as mock_genai_module:
            mock_genai_module.GenerativeModel.return_value = mock_model
            
            service = AIService()
            
            with pytest.raises(AiServiceError, match="Failed to parse structured data from AI response"):
                await service.get_structured_data("Test invoice text")
    
    @pytest.mark.asyncio
    async def test_get_structured_data_validation_error(self, mock_settings):
        """Test error handling for data validation errors"""
        from app.services.ai_service import AIService
        from app.exceptions import AiServiceError
        
        # Mock AI to return JSON that fails validation
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"invoice_number": "INV-123", "total": "invalid_number"}'  # Invalid total
        mock_model.generate_content.return_value = mock_response
        
        with patch('app.services.ai_service.genai') as mock_genai_module:
            mock_genai_module.GenerativeModel.return_value = mock_model
            
            service = AIService()
            
            with pytest.raises(AiServiceError, match="AI response data failed validation"):
                await service.get_structured_data("Test invoice text")
    
    @pytest.mark.asyncio
    async def test_get_structured_data_api_error(self, mock_settings):
        """Test error handling for API errors"""
        from app.services.ai_service import AIService
        from app.exceptions import AiServiceError
        
        # Mock AI to raise an exception
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API connection error")
        
        with patch('app.services.ai_service.genai') as mock_genai_module:
            mock_genai_module.GenerativeModel.return_value = mock_model
            
            service = AIService()
            
            with pytest.raises(AiServiceError):
                await service.get_structured_data("Test invoice text")
    
    def test_fallback_placeholders(self, mock_settings, mock_genai):
        """Test that fallback placeholders are implemented"""
        from app.services.ai_service import AIService
        
        service = AIService()
        
        with pytest.raises(NotImplementedError, match="OpenAI fallback not implemented yet"):
            service._fallback_to_openai("test text")
            
        with pytest.raises(NotImplementedError, match="Claude fallback not implemented yet"):
            service._fallback_to_claude("test text")


class TestPromptManager:
    """Test cases for PromptManager"""
    
    def test_prompt_manager_initialization(self):
        """Test PromptManager initializes correctly"""
        from app.prompts.invoice_prompts import PromptManager
        
        manager = PromptManager()
        assert manager.base_template is not None
        assert "invoice_text" in manager.base_template
        assert "Response (valid JSON only)" in manager.base_template
    
    def test_get_extraction_prompt_basic(self):
        """Test basic prompt generation"""
        from app.prompts.invoice_prompts import PromptManager
        
        manager = PromptManager()
        invoice_text = "Invoice #12345\nVendor: Test Company\nTotal: $100.00"
        
        prompt = manager.get_extraction_prompt(invoice_text)
        
        assert invoice_text in prompt
        assert "invoice_number" in prompt
        assert "vendor_name" in prompt
        assert "total" in prompt
        assert "Response (valid JSON only)" in prompt
    
    def test_get_extraction_prompt_with_table_data(self):
        """Test prompt generation with table data"""
        from app.prompts.invoice_prompts import PromptManager
        
        manager = PromptManager()
        invoice_text = "Invoice #12345"
        table_data = {
            "tables": [
                "Item | Qty | Price\nWidget | 2 | $10.00",
                "Service | Hours | Rate\nConsulting | 5 | $50.00"
            ]
        }
        
        prompt = manager.get_extraction_prompt(invoice_text, table_data)
        
        assert invoice_text in prompt
        assert "Table Data:" in prompt
        assert "Table 1:" in prompt
        assert "Table 2:" in prompt
        assert "Widget | 2 | $10.00" in prompt
        assert "Consulting | 5 | $50.00" in prompt
    
    def test_get_extraction_prompt_empty_table_data(self):
        """Test prompt generation with empty table data"""
        from app.prompts.invoice_prompts import PromptManager
        
        manager = PromptManager()
        invoice_text = "Invoice #12345"
        table_data = {}
        
        prompt = manager.get_extraction_prompt(invoice_text, table_data)
        
        assert invoice_text in prompt
        assert "Table Data:" not in prompt
    
    def test_get_extraction_prompt_no_table_data(self):
        """Test prompt generation with None table data"""
        from app.prompts.invoice_prompts import PromptManager
        
        manager = PromptManager()
        invoice_text = "Invoice #12345"
        
        prompt = manager.get_extraction_prompt(invoice_text, None)
        
        assert invoice_text in prompt
        assert "Table Data:" not in prompt