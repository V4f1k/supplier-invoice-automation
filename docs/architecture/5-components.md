# 5. Components

This section breaks down the application into its major logical components. This design is based on the repository structure proposed in the PRD and the Repository Pattern, promoting a clear separation of concerns and making the system more modular and testable.

## 5.1. API Handler (`main.py`)

- **Responsibility:** Acts as the main entry point for the service. It defines the FastAPI application, configures the `/extract` and `/health` endpoints, handles incoming HTTP requests, and orchestrates the calls to other services.
- **Key Interfaces:**
    - `POST /extract`: Receives the file and returns the structured data.
    - `GET /health`: Returns a health status.
- **Dependencies:** Configuration Service, Cache Service, OCR Service, AI Service.

## 5.2. Configuration Service (`config.py`)

- **Responsibility:** Manages all application settings and secrets (e.g., API keys, Redis URL). It loads configuration from environment variables to ensure no sensitive data is hardcoded.
- **Key Interfaces:** Provides functions or objects to access configuration values.
- **Dependencies:** None.

## 5.3. OCR Service (`services/ocr.py`)

- **Responsibility:** Encapsulates all logic related to the Surya-OCR library. It takes a raw file (PDF/image) and performs the OCR and table detection.
- **Key Interfaces:** A function like `extract_text_and_tables(file)`.
- **Dependencies:** Surya-OCR library.

## 5.4. AI Service (`services/ai.py`)

- **Responsibility:** Manages all interactions with the external AI provider (Gemini). It takes the text and table data from the OCR Service, formats it using prompts from the Prompt Manager, and calls the AI API to get structured data. It also handles the logic for any fallback providers.
- **Key Interfaces:** A function like `get_structured_data(ocr_output)`.
- **Dependencies:** Google AI Client, Prompt Manager.

## 5.5. Cache Service (`services/cache.py`)

- **Responsibility:** Handles all read and write operations to the Redis cache. It provides simple methods for getting, setting, and checking for the existence of cached invoice data.
- **Key Interfaces:** Functions like `get_from_cache(key)`, `set_in_cache(key, value)`.
- **Dependencies:** redis-py library.

## 5.6. Prompt Manager (`prompts/invoice_cz.py`)

- **Responsibility:** Stores and manages the prompt templates used to guide the AI model's extraction process. This separation allows for easier tuning and management of prompts without changing application code.
- **Key Interfaces:** Provides functions or constants that return formatted prompt strings.
- **Dependencies:** None.

---
