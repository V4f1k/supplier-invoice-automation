"""API v1 endpoints"""

import tempfile
import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger

from app.services.ocr_service import extract_text
from app.services.cache_service import cache_service
from app.services.ai_service import get_ai_service
from app.schemas import TextExtractionResponse, ExtractionResponse
from app.utils import calculate_file_hash
from app.exceptions import InvalidFileTypeError, FileProcessingError, OcrError, AiServiceError

router = APIRouter()

# Supported file types
SUPPORTED_FILE_TYPES = {
    "application/pdf",
    "image/png", 
    "image/jpeg",
    "image/jpg"
}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


class N8NBinaryFile(BaseModel):
    """Model for N8N binary file data"""
    data: str  # Base64 encoded file data
    mimeType: Optional[str] = "application/pdf"
    fileName: Optional[str] = "invoice.pdf"


class N8NRequest(BaseModel):
    """Model for N8N request with binary file"""
    file: Optional[N8NBinaryFile] = None
    # Alternative field names N8N might use
    file_base64: Optional[str] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None


class SimpleN8NRequest(BaseModel):
    """Simplified model for N8N HTTP Request node"""
    data: str  # Required: Base64 encoded file data
    filename: Optional[str] = "invoice.pdf"
    mimetype: Optional[str] = "application/pdf"


@router.get("/health")
async def health_check():
    """Service health check endpoint"""
    return {"status": "ok"}


@router.get("/health/detailed")
async def health_check_detailed():
    """Detailed health check endpoint for N8N monitoring"""
    
    # Test cache service
    cache_status = "ok"
    try:
        await cache_service.get("health_check")
        cache_status = "ok"
    except Exception as e:
        logger.warning(f"Cache health check failed: {e}")
        cache_status = "degraded"
    
    # Test AI service availability
    ai_status = "ok"
    try:
        ai_service = get_ai_service()
        # Just check if service initializes properly
        ai_status = "ok" if ai_service else "error"
    except Exception as e:
        logger.warning(f"AI service health check failed: {e}")
        ai_status = "error"
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "cache": cache_status,
            "ai_service": ai_status,
            "ocr": "ok"  # OCR is file-based, always available
        },
        "endpoints": [
            "/health",
            "/health/detailed", 
            "/extract",
            "/extract-n8n",
            "/extract-simple"
        ],
        "supported_file_types": list(SUPPORTED_FILE_TYPES),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024)
    }


@router.post("/extract", response_model=ExtractionResponse)
async def extract_invoice_text(
    file: UploadFile = File(...)
) -> ExtractionResponse:
    """
    Extract structured data from an uploaded invoice file (PDF, PNG, JPG)
    
    Args:
        file: Uploaded file in multipart/form-data format
        
    Returns:
        JSON response containing structured invoice data
        
    Raises:
        HTTPException: If file validation fails or processing errors occur
    """
    
    # Validate file type - handle N8N sending multipart/form-data as content_type
    actual_content_type = file.content_type
    
    # If N8N sends multipart/form-data, try to detect from filename
    if actual_content_type == "multipart/form-data" and file.filename:
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        ext_to_mime = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg'
        }
        actual_content_type = ext_to_mime.get(file_ext, actual_content_type)
        logger.info(f"Detected file type from extension: {actual_content_type}")
    
    if actual_content_type not in SUPPORTED_FILE_TYPES:
        logger.warning(f"Unsupported file type: {actual_content_type} (original: {file.content_type})")
        raise InvalidFileTypeError(
            file_type=actual_content_type,
            supported_types=list(SUPPORTED_FILE_TYPES)
        )
    
    # Read file content to check size and calculate hash
    try:
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes")
            raise FileProcessingError(
                message=f"File too large. Maximum size allowed: {MAX_FILE_SIZE // (1024*1024)}MB",
                detail=f"File size: {file_size} bytes"
            )
        
        # Calculate file hash for caching
        file_hash = calculate_file_hash(file_content)
        logger.info(f"File hash calculated: {file_hash[:8]}... for {file.filename}")
        
        # Check cache first
        cached_result = await cache_service.get(file_hash)
        if cached_result:
            logger.info(f"Returning cached result for {file.filename}")
            return ExtractionResponse(**cached_result)
        
        # Reset file pointer
        await file.seek(0)
        
    except FileProcessingError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise FileProcessingError(
            message="Error reading uploaded file",
            detail=str(e)
        )
    
    # Create temporary file for processing
    temp_file_path = None
    try:
        # Determine file extension based on content type
        file_extension = ""
        if file.content_type == "application/pdf":
            file_extension = ".pdf"
        elif file.content_type in ["image/png"]:
            file_extension = ".png"
        elif file.content_type in ["image/jpeg", "image/jpg"]:
            file_extension = ".jpg"
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=file_extension
        ) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(file_content)
        
        logger.info(f"Processing file: {file.filename} ({file.content_type}) - {file_size} bytes")
        
        # Extract text using OCR service
        extracted_text = await extract_text(temp_file_path)
        
        logger.info(f"Successfully extracted {len(extracted_text)} characters from {file.filename}")
        
        # Process with AI service to get structured data
        try:
            ai_service = get_ai_service()
            structured_data = await ai_service.get_structured_data(extracted_text)
            logger.info(f"Successfully processed structured data from {file.filename}")
            
            # Convert InvoiceData to ExtractionResponse format
            response_data = ExtractionResponse(
                invoice_number=structured_data.invoice_number,
                invoice_date=structured_data.invoice_date,
                due_date=structured_data.due_date,
                vendor_name=structured_data.vendor_name,
                vendor_address=structured_data.vendor_address,
                customer_name=structured_data.customer_name,
                customer_address=structured_data.customer_address,
                subtotal=structured_data.subtotal,
                tax=structured_data.tax,
                total=structured_data.total,
                currency=structured_data.currency,
                items=structured_data.items
            )
            
            # Cache the structured result for future requests
            cache_data = response_data.model_dump()
            await cache_service.set(file_hash, cache_data)
            
            return response_data
            
        except AiServiceError:
            # Re-raise AI service errors - they will be handled by the exception middleware
            raise
        
    except (InvalidFileTypeError, FileProcessingError, OcrError, AiServiceError):
        # Re-raise our custom exceptions - they will be handled by the exception middleware
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {e}")
        raise OcrError(
            message="Failed to process file",
            detail=str(e)
        )
        
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")


@router.post("/extract-simple", response_model=ExtractionResponse, operation_id="extract_invoice_simple_n8n")
async def extract_invoice_simple(request: SimpleN8NRequest) -> ExtractionResponse:
    """
    Simplified N8N endpoint for HTTP Request node integration
    
    Accepts simple JSON with base64 data, filename, and mimetype.
    Designed specifically for N8N HTTP Request node compatibility.
    
    Args:
        request: Simple request with required data field and optional filename/mimetype
        
    Returns:
        JSON response containing structured invoice data
    """
    
    # Validate mimetype
    if request.mimetype not in SUPPORTED_FILE_TYPES:
        logger.warning(f"Unsupported file type: {request.mimetype}")
        raise InvalidFileTypeError(
            file_type=request.mimetype,
            supported_types=list(SUPPORTED_FILE_TYPES)
        )
    
    # Decode base64 data
    try:
        # Remove data URL prefix if present (e.g., "data:application/pdf;base64,")
        base64_data = request.data
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',', 1)[1]
        
        file_content = base64.b64decode(base64_data)
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes")
            raise FileProcessingError(
                message=f"File too large. Maximum size allowed: {MAX_FILE_SIZE // (1024*1024)}MB",
                detail=f"File size: {file_size} bytes"
            )
        
    except Exception as e:
        logger.error(f"Error decoding base64 data: {e}")
        raise FileProcessingError(
            message="Invalid base64 data",
            detail=str(e)
        )
    
    # Calculate file hash for caching
    file_hash = calculate_file_hash(file_content)
    logger.info(f"File hash calculated: {file_hash[:8]}... for {request.filename}")
    
    # Check cache first
    cached_result = await cache_service.get(file_hash)
    if cached_result:
        logger.info(f"Returning cached result for {request.filename}")
        return ExtractionResponse(**cached_result)
    
    # Create temporary file for processing
    temp_file_path = None
    
    try:
        # Determine file extension from mimetype
        extension = ".pdf"
        if "png" in request.mimetype:
            extension = ".png"
        elif "jpg" in request.mimetype or "jpeg" in request.mimetype:
            extension = ".jpg"
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
            
        logger.info(f"Processing file: {request.filename} ({request.mimetype}) - {file_size} bytes")
        
        # Extract text using OCR
        extracted_text = await extract_text(temp_file_path)
        logger.info(f"Successfully extracted {len(extracted_text)} characters from {request.filename}")
        
        # Process with AI service to get structured data
        ai_service = get_ai_service()
        structured_data = await ai_service.get_structured_data(extracted_text)
        logger.info(f"Successfully processed structured data from {request.filename}")
        
        # Convert InvoiceData to ExtractionResponse format
        response_data = ExtractionResponse(
            invoice_number=structured_data.invoice_number,
            invoice_date=structured_data.invoice_date,
            due_date=structured_data.due_date,
            vendor_name=structured_data.vendor_name,
            vendor_address=structured_data.vendor_address,
            customer_name=structured_data.customer_name,
            customer_address=structured_data.customer_address,
            subtotal=structured_data.subtotal,
            tax=structured_data.tax,
            total=structured_data.total,
            currency=structured_data.currency,
            items=structured_data.items
        )
        
        # Cache the structured result for future requests
        cache_data = response_data.model_dump()
        await cache_service.set(file_hash, cache_data)
        
        return response_data
        
    except (InvalidFileTypeError, FileProcessingError, OcrError, AiServiceError):
        # Re-raise our custom exceptions - they will be handled by the exception middleware
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error processing {request.filename}: {e}")
        raise OcrError(
            message="Failed to process file",
            detail=str(e)
        )
        
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")


@router.post("/extract-n8n", response_model=ExtractionResponse)
async def extract_invoice_n8n(request: N8NRequest) -> ExtractionResponse:
    """
    Extract structured data from N8N binary file format
    
    Args:
        request: N8N request with base64 encoded file
        
    Returns:
        JSON response containing structured invoice data
    """
    
    # Extract base64 data from various possible fields
    base64_data = None
    filename = "invoice.pdf"
    content_type = "application/pdf"
    
    # Try to get data from N8N binary file format
    if request.file and request.file.data:
        base64_data = request.file.data
        filename = request.file.fileName or filename
        content_type = request.file.mimeType or content_type
    # Try alternative field names
    elif request.file_base64:
        base64_data = request.file_base64
        filename = request.filename or filename
        content_type = request.content_type or content_type
    else:
        raise FileProcessingError(
            message="No file data provided",
            detail="Expected base64 encoded file data in 'file.data' or 'file_base64' field"
        )
    
    # Decode base64 data
    try:
        # Remove data URL prefix if present
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',')[1]
        
        file_content = base64.b64decode(base64_data)
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes")
            raise FileProcessingError(
                message=f"File too large. Maximum size allowed: {MAX_FILE_SIZE // (1024*1024)}MB",
                detail=f"File size: {file_size} bytes"
            )
        
    except Exception as e:
        logger.error(f"Error decoding base64 data: {e}")
        raise FileProcessingError(
            message="Invalid base64 data",
            detail=str(e)
        )
    
    # Calculate file hash for caching
    file_hash = calculate_file_hash(file_content)
    logger.info(f"File hash calculated: {file_hash[:8]}... for {filename}")
    
    # Check cache first
    cached_result = await cache_service.get(file_hash)
    if cached_result:
        logger.info(f"Returning cached result for {filename}")
        return ExtractionResponse(**cached_result)
    
    # Create temporary file for processing
    temp_file_path = None
    
    try:
        # Determine file extension from content type
        extension = ".pdf"
        if "png" in content_type:
            extension = ".png"
        elif "jpg" in content_type or "jpeg" in content_type:
            extension = ".jpg"
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
            
        logger.info(f"Processing file: {filename} ({content_type}) - {file_size} bytes")
        
        # Extract text using OCR
        try:
            extracted_text = await extract_text(temp_file_path)
            logger.debug(f"OCR extracted {len(extracted_text)} characters")
            
        except OcrError:
            # Re-raise OCR errors - they will be handled by the exception middleware
            raise
        
        # Process with AI
        try:
            ai_service = get_ai_service()
            response_data = await ai_service.extract_invoice_data(extracted_text)
            
            # Cache the result
            if hasattr(response_data, 'model_dump'):
                cache_data = response_data.model_dump()
            else:
                cache_data = response_data if isinstance(response_data, dict) else response_data.__dict__
            await cache_service.set(file_hash, cache_data)
            
            return response_data
            
        except AiServiceError:
            # Re-raise AI service errors - they will be handled by the exception middleware
            raise
        
    except (FileProcessingError, OcrError, AiServiceError):
        # Re-raise our custom exceptions
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error processing {filename}: {e}")
        raise OcrError(
            message="Failed to process file",
            detail=str(e)
        )
        
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")