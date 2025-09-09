"""Gemini AI service with retry and circuit breaker patterns"""

import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
import google.generativeai as genai

from app.config import settings
from app.exceptions import AiServiceError, CircuitBreakerOpenError
from app.prompts.invoice_prompts import PromptManager
from app.schemas import InvoiceData


class CircuitBreaker:
    """Simple circuit breaker implementation for AI service"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN state")
            else:
                logger.warning("Circuit breaker is OPEN, failing fast")
                raise CircuitBreakerOpenError("AI Service")
        
        try:
            # Handle both sync and async functions
            result = func(*args, **kwargs)
            if hasattr(result, '__await__'):
                result = await result
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout)
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        if self.state == "HALF_OPEN":
            logger.info("Circuit breaker reset to CLOSED state after successful call")
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failure in circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")


def clean_ai_response(response_text: str) -> str:
    """
    Clean AI response by removing markdown code blocks and extra whitespace
    
    Args:
        response_text: Raw response from AI model
        
    Returns:
        Cleaned JSON string
    """
    # Remove leading/trailing whitespace
    cleaned_text = response_text.strip()
    
    # Remove markdown code blocks if present
    # Pattern matches: ```json ... ``` or ```... ```
    markdown_pattern = r'```(?:json)?\s*(.*?)\s*```'
    match = re.search(markdown_pattern, cleaned_text, re.DOTALL)
    
    if match:
        cleaned_text = match.group(1).strip()
        logger.debug("Removed markdown code blocks from AI response")
    
    return cleaned_text


class AIService:
    """Gemini AI service with retry and circuit breaker patterns"""
    
    def __init__(self):
        # Initialize Gemini AI client
        if not settings.google_api_key:
            raise AiServiceError("Google API key not configured")
        
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            expected_exception=(AiServiceError, Exception)
        )
        
        # Initialize prompt manager
        self.prompt_manager = PromptManager()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((AiServiceError,)),
        reraise=True
    )
    async def _call_gemini_api(self, prompt: str) -> str:
        """Make API call to Gemini with retry logic"""
        try:
            logger.info("Calling Gemini API for invoice extraction")
            
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise AiServiceError("Empty response from Gemini API")
            
            logger.info("Successfully received response from Gemini API")
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            # Determine if this is a transient error that should be retried
            if self._is_transient_error(e):
                raise AiServiceError(f"Transient error from Gemini API: {str(e)}")
            else:
                raise AiServiceError(f"Permanent error from Gemini API: {str(e)}")
    
    def _is_transient_error(self, error: Exception) -> bool:
        """Determine if error is transient and should be retried"""
        error_str = str(error).lower()
        transient_indicators = [
            "503", "502", "504", "500",  # Server errors
            "429",  # Rate limit
            "timeout",
            "connection",
            "network",
            "quota exceeded"
        ]
        return any(indicator in error_str for indicator in transient_indicators)
    
    async def extract_invoice_data(self, invoice_text: str) -> Dict[str, Any]:
        """Extract structured data from invoice text"""
        if not invoice_text or not invoice_text.strip():
            raise AiServiceError("Empty or invalid invoice text provided")
        
        prompt = self.prompt_manager.get_extraction_prompt(invoice_text)
        
        try:
            # Use circuit breaker to protect against cascading failures
            response_text = await self.circuit_breaker.call(
                self._call_gemini_api, 
                prompt
            )
            
            # Check for empty response
            if not response_text or not response_text.strip():
                raise AiServiceError("Empty response from AI service")
            
            # Debug: Log raw AI response
            logger.debug(f"Raw AI response: {response_text}")
            
            # Clean and parse JSON response
            try:
                cleaned_response = clean_ai_response(response_text)
                logger.debug(f"Cleaned AI response: {cleaned_response}")
                extracted_data = json.loads(cleaned_response)
                logger.info("Successfully parsed invoice data from AI response")
                return extracted_data
            
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from AI response: {e}")
                logger.debug(f"Raw AI response: {response_text}")
                raise AiServiceError(
                    "Failed to parse structured data from AI response",
                    detail=f"JSON parse error: {str(e)}"
                )
                
        except CircuitBreakerOpenError:
            # Re-raise circuit breaker errors without modification
            raise
        
        except AiServiceError:
            # Re-raise AI service errors without modification
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error in AI service: {e}")
            raise AiServiceError(f"Unexpected error: {str(e)}")
    
    async def get_structured_data(self, text: str, table_data: Optional[Dict[str, Any]] = None) -> InvoiceData:
        """
        Extract structured data from invoice text using Gemini AI
        
        Args:
            text: OCR extracted text from invoice
            table_data: Optional table data extracted from invoice
            
        Returns:
            Validated InvoiceData object
            
        Raises:
            AiServiceError: If extraction or validation fails
        """
        if not text or not text.strip():
            raise AiServiceError("Empty or invalid invoice text provided")
        
        # Debug: Log the OCR text we received
        logger.debug(f"OCR extracted text (first 500 chars): {text[:500]}")
        
        # Get structured prompt from PromptManager
        prompt = self.prompt_manager.get_extraction_prompt(text, table_data)
        logger.debug(f"Generated prompt length: {len(prompt)} characters")
        
        try:
            # Use circuit breaker to protect against cascading failures
            response_text = await self.circuit_breaker.call(
                self._call_gemini_api, 
                prompt
            )
            
            # Check for empty response
            if not response_text or not response_text.strip():
                raise AiServiceError("Empty response from AI service")
            
            # Debug: Log raw AI response
            logger.debug(f"Raw AI response: {response_text}")
            
            # Clean and parse JSON response
            try:
                cleaned_response = clean_ai_response(response_text)
                logger.debug(f"Cleaned AI response: {cleaned_response}")
                extracted_data = json.loads(cleaned_response)
                logger.info("Successfully parsed invoice data from AI response")
                
                # Validate against InvoiceData schema
                try:
                    validated_data = InvoiceData(**extracted_data)
                    logger.info("Successfully validated invoice data against schema")
                    return validated_data
                    
                except Exception as validation_error:
                    logger.error(f"Data validation failed: {validation_error}")
                    raise AiServiceError(
                        "AI response data failed validation",
                        detail=f"Validation error: {str(validation_error)}"
                    )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from AI response: {e}")
                logger.debug(f"Raw AI response: {response_text}")
                raise AiServiceError(
                    "Failed to parse structured data from AI response",
                    detail=f"JSON parse error: {str(e)}"
                )
                
        except CircuitBreakerOpenError:
            # Re-raise circuit breaker errors without modification
            raise
        
        except AiServiceError:
            # Re-raise AI service errors without modification
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error in AI service: {e}")
            raise AiServiceError(f"Unexpected error: {str(e)}")
    
    # Placeholder for fallback logic to other AI providers
    def _fallback_to_openai(self, text: str) -> InvoiceData:
        """
        Placeholder for OpenAI fallback implementation
        
        This method would implement fallback logic to OpenAI's API
        when Gemini is unavailable. Implementation not in scope for this story.
        """
        raise NotImplementedError("OpenAI fallback not implemented yet")
    
    def _fallback_to_claude(self, text: str) -> InvoiceData:
        """
        Placeholder for Claude fallback implementation
        
        This method would implement fallback logic to Anthropic's Claude API
        when Gemini is unavailable. Implementation not in scope for this story.
        """
        raise NotImplementedError("Claude fallback not implemented yet")


# Global AI service instance - lazy loaded
ai_service: Optional[AIService] = None

def get_ai_service() -> AIService:
    """Get or create the AI service instance"""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service