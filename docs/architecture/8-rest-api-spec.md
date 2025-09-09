# 8. REST API Spec

This specification is based on the API details in the PRD and our refined data models.

```yaml
openapi: 3.0.1
info:
  title: "Invoice OCR & AI Extraction Service"
  description: "An API for extracting structured data from invoice files (PDF, PNG, JPG)."
  version: "1.0.0"
servers:
  - url: "http://localhost:8000"
    description: "Development server"
paths:
  /extract:
    post:
      summary: "Extracts data from an invoice file"
      operationId: "extract_invoice_data"
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                  description: "The invoice file (PDF, PNG, or JPG) to process."
      responses:
        '200':
          description: "Successful extraction"
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExtractionResponse'
        '400':
          description: "Bad Request (e.g., invalid file type, password protected)"
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiError'
        '500':
          description: "Internal Server Error"
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiError'
  /health:
    get:
      summary: "Service Health Check"
      operationId: "health_check"
      responses:
        '200':
          description: "Service is healthy"
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "ok"

components:
  schemas:
    ExtractionResponse:
      type: object
      properties:
        success:
          type: boolean
          example: true
        confidence:
          type: number
          format: float
          example: 0.92
        cached:
          type: boolean
          example: false
        data:
          $ref: '#/components/schemas/InvoiceData'
    ApiError:
      type: object
      properties:
        success:
          type: boolean
          example: false
        error:
          type: string
          example: "Error description"
        requestId:
          type: string
          format: uuid
    InvoiceData:
      type: object
      properties:
        supplier:
          $ref: '#/components/schemas/Supplier'
        customer:
          $ref: '#/components/schemas/Customer'
        invoice:
          $ref: '#/components/schemas/Invoice'
        totals:
          $ref: '#/components/schemas/Totals'
        currency:
          type: string
          example: "CZK"
        items:
          type: array
          items:
            $ref: '#/components/schemas/Item'
    Supplier:
      type: object
      properties:
        name: { type: string }
        address: { type: string }
        ico: { type: string }
        dic: { type: string }
        iban: { type: string }
    Customer:
      type: object
      properties:
        name: { type: string }
        billingAddress: { type: string }
    Invoice:
      type: object
      properties:
        invoiceNumber: { type: string }
        issueDate: { type: string, format: date }
        dueDate: { type: string, format: date }
        dateOfTaxableSupply: { type: string, format: date }
        variableSymbol: { type: string }
    Totals:
      type: object
      properties:
        withoutTax: { type: number, format: float }
        tax: { type: number, format: float }
        withTax: { type: number, format: float }
    Item:
      type: object
      properties:
        name: { type: string }
        quantity: { type: number, format: float }
        unitPrice: { type: number, format: float }
        vatRate: { type: number, format: float }
        lineTotal: { type: number, format: float }
```

---
