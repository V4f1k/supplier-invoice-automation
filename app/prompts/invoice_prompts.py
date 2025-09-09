"""Prompt templates for AI service"""

from typing import Optional, Dict, Any


INVOICE_EXTRACTION_PROMPT = """
You are an expert at extracting structured data from invoice text. 
Please extract the following information from the given invoice text and return it in JSON format:

- invoice_number: The invoice or document number
- invoice_date: Date of the invoice (format: YYYY-MM-DD)
- due_date: Payment due date (format: YYYY-MM-DD)  
- vendor_name: Name of the vendor/supplier
- vendor_address: Vendor's address
- customer_name: Customer name
- customer_address: Customer address
- subtotal: Subtotal amount (numeric)
- tax: Tax amount (numeric)
- total: Total amount (numeric)
- currency: Currency code (e.g., USD, EUR)
- items: Array of line items with description, quantity, unit_price, total_price

If any field is not found or unclear, return null for that field.

Invoice Text:
{invoice_text}

{table_data}

Response (valid JSON only):
"""


class PromptManager:
    """Manages prompt templates for AI service"""
    
    def __init__(self):
        self.base_template = INVOICE_EXTRACTION_PROMPT
    
    def get_extraction_prompt(
        self, 
        invoice_text: str, 
        table_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Creates a structured prompt for invoice data extraction
        
        Args:
            invoice_text: The OCR extracted text from the invoice
            table_data: Optional table data extracted from the invoice
            
        Returns:
            Formatted prompt string ready for AI processing
        """
        # Format table data if provided
        table_section = ""
        if table_data and table_data.get("tables"):
            table_section = "\nTable Data:\n"
            for i, table in enumerate(table_data["tables"]):
                table_section += f"Table {i+1}:\n{table}\n"
        
        return self.base_template.format(
            invoice_text=invoice_text,
            table_data=table_section
        )