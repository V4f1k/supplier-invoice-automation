"""Main FastAPI application"""

import uuid
from typing import Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.v1 import endpoints
from app.exceptions import AppException
from app.schemas import ApiError

app = FastAPI(
    title="Invoice OCR & AI Extraction Service",
    description="An API for extracting structured data from invoice files (PDF, PNG, JPG).",
    version="1.0.0"
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to all requests for logging purposes"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add request ID to logger context
    with logger.contextualize(request_id=request_id):
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log the exception with context
    logger.error(
        "Application error occurred: {}",
        exc.message,
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__,
            "status_code": exc.status_code,
            "detail": str(exc.detail) if exc.detail else None,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Create error response matching ApiError schema
    error_response = ApiError(
        error=exc.message,
        error_code=exc.error_code,
        detail=exc.detail
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True, mode='json')
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        "HTTP exception: {}",
        exc.detail,
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Convert to ApiError format
    error_response = ApiError(
        error="HTTP Error",
        error_code="HTTP_ERROR",
        detail=exc.detail
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True, mode='json')
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log the full exception details
    logger.error(
        "Unhandled exception occurred: {}",
        str(exc),
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Create generic error response
    error_response = ApiError(
        error="Internal Server Error",
        error_code="INTERNAL_ERROR",
        detail="An unexpected error occurred. Please try again later."
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(exclude_none=True, mode='json')
    )


# Include API routers
app.include_router(endpoints.router, prefix="", tags=["v1"])