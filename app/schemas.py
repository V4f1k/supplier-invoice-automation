"""Pydantic models for data validation"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class ApiError(BaseModel):
    """Standard error response model"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ApiSuccess(BaseModel):
    """Standard success response wrapper"""
    success: bool = True
    data: dict
    timestamp: datetime = Field(default_factory=datetime.now)


class TextExtractionResponse(BaseModel):
    """Response model for OCR text extraction"""
    text: str
    filename: str
    file_type: str
    file_size: int
    text_length: int
    cached: bool = False


class ExtractedItem(BaseModel):
    """Individual line item from invoice"""
    description: str
    quantity: float
    unit_price: float
    total_price: float


class InvoiceData(BaseModel):
    """Structured invoice data model for AI validation"""
    invoice_number: str
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    vendor_name: str
    vendor_address: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    subtotal: float
    tax: float
    total: float
    currency: str = "USD"
    items: List[ExtractedItem] = []


class ExtractionResponse(BaseModel):
    """Response model for invoice extraction"""
    invoice_number: str
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    vendor_name: str
    vendor_address: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    subtotal: float
    tax: float
    total: float
    currency: str = "USD"
    items: List[ExtractedItem] = []