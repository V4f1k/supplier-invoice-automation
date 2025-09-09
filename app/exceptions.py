"""Custom exceptions for the invoice OCR service"""

from typing import Optional


class AppException(Exception):
    """Base exception for all application errors"""
    
    def __init__(self, message: str, status_code: int = 500, detail: Optional[str] = None, error_code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(self.message)


class InvalidFileTypeError(AppException):
    """Raised when an unsupported file type is uploaded"""
    
    def __init__(self, file_type: str, supported_types: list[str]):
        message = f"Invalid file type: {file_type}"
        detail = f"Supported types: {', '.join(supported_types)}"
        super().__init__(message, status_code=400, detail=detail, error_code="INVALID_FILE_TYPE")


class OcrError(AppException):
    """Raised when OCR processing fails"""
    
    def __init__(self, message: str = "OCR processing failed", detail: Optional[str] = None):
        super().__init__(message, status_code=500, detail=detail, error_code="OCR_ERROR")


class AiServiceError(AppException):
    """Raised when AI service fails"""
    
    def __init__(self, message: str = "AI service error", detail: Optional[str] = None, status_code: int = 500):
        super().__init__(message, status_code=status_code, detail=detail, error_code="AI_SERVICE_ERROR")


class CacheError(AppException):
    """Raised when cache operations fail"""
    
    def __init__(self, message: str = "Cache operation failed", detail: Optional[str] = None):
        super().__init__(message, status_code=500, detail=detail, error_code="CACHE_ERROR")


class FileProcessingError(AppException):
    """Raised when file processing fails"""
    
    def __init__(self, message: str = "File processing failed", detail: Optional[str] = None):
        super().__init__(message, status_code=400, detail=detail, error_code="FILE_PROCESSING_ERROR")


class CircuitBreakerOpenError(AiServiceError):
    """Raised when circuit breaker is open"""
    
    def __init__(self, service_name: str = "AI Service"):
        message = f"{service_name} is temporarily unavailable"
        detail = "Circuit breaker is open due to repeated failures. Please try again later."
        super().__init__(message, detail=detail, status_code=503)
        self.error_code = "CIRCUIT_BREAKER_OPEN"