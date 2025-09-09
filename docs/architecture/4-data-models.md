# 4. Data Models

The following conceptual data models are derived directly from the `POST /extract` API response specification in the PRD and user feedback. They will serve as the blueprint for the Pydantic models in `app/models.py`.

## 4.1. Supplier

- **Purpose:** Represents the entity that issued the invoice.
- **Key Attributes:**
    - `name`: string - The legal name of the supplier.
    - `address`: string - The full address of the supplier.
    - `ico`: string - The supplier's business identification number (IČO).
    - `dic`: string - The supplier's tax identification number (DIČ).
    - `iban`: string - The supplier's bank account number in IBAN format.
- **Relationships:** A child of the `InvoiceData` model.

## 4.2. Customer

- **Purpose:** Represents the entity receiving the invoice (the bill-to party).
- **Key Attributes:**
    - `name`: string - The name of the customer.
    - `billingAddress`: string - The customer's full billing address.
- **Relationships:** A child of the `InvoiceData` model.

## 4.3. Invoice

- **Purpose:** Contains the primary identification and date information for the invoice document.
- **Key Attributes:**
    - `invoiceNumber`: string - The unique identifier for the invoice.
    - `issueDate`: string - The date the invoice was issued (to be normalized to ISO 8601 format).
    - `dueDate`: string - The date the payment is due (to be normalized to ISO 8601 format).
    - `dateOfTaxableSupply`: string - The date of taxable supply (DUZP), normalized to ISO 8601.
    - `variableSymbol`: string - The variable symbol for the payment.
- **Relationships:** A child of the `InvoiceData` model.

## 4.4. Totals

- **Purpose:** Aggregates the key financial totals for the invoice.
- **Key Attributes:**
    - `withoutTax`: float - The total amount excluding tax.
    - `tax`: float - The total tax amount.
    - `withTax`: float - The total amount including tax.
- **Relationships:** A child of the `InvoiceData` model.

## 4.5. Item

- **Purpose:** Represents a single line item from the invoice's itemization table.
- **Key Attributes:**
    - `name`: string - The description of the item or service.
    - `quantity`: float - The quantity of the item.
    - `unitPrice`: float - The price per unit, excluding tax.
    - `vatRate`: float - The VAT rate applied to the item (e.g., 21.0 for 21%).
    - `lineTotal`: float - The total price for the line item.
- **Relationships:** A list of `Item` models is a child of the `InvoiceData` model.

## 4.6. InvoiceData (Root Model)

- **Purpose:** The main container model that aggregates all structured data extracted from an invoice.
- **Key Attributes:**
    - `supplier`: Supplier - The supplier information.
    - `customer`: Customer - The customer information.
    - `invoice`: Invoice - The core invoice details.
    - `totals`: Totals - The financial totals.
    - `currency`: string - The currency of the financial amounts (e.g., "CZK", "EUR").
    - `items`: List[Item] - A list of all line items.
- **Relationships:** The root entity composed of the other data models.

---
