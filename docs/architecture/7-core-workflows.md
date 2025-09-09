# 7. Core Workflows

This diagram illustrates the sequence of events for the primary success path: processing a new invoice that is not yet in the cache.

## 7.1. Invoice Extraction (Cache Miss)

```mermaid
sequenceDiagram
    participant N8N as n8n Workflow
    participant API as API Handler (main.py)
    participant Cache as Cache Service
    participant OCR as OCR Service
    participant AI as AI Service
    participant Gemini as Google Gemini API
    participant Redis

    N8N->>+API: POST /extract (file)
    API->>+Cache: get_from_cache(file_hash)
    Cache->>+Redis: GET file_hash
    Redis-->>-Cache: null
    Cache-->>-API: null

    API->>+OCR: extract_text_and_tables(file)
    OCR-->>-API: ocr_result

    API->>+AI: get_structured_data(ocr_result)
    AI->>+Gemini: generate_content(prompt)
    Gemini-->>-AI: structured_json
    AI-->>-API: normalized_data

    API->>+Cache: set_in_cache(file_hash, data)
    Cache->>+Redis: SET file_hash data
    Redis-->>-Cache: OK
    Cache-->>-API: OK

    API-->>-N8N: 200 OK (JSON data)
```

**Other Workflows:**

-   **Cache Hit:** If the `Cache Service` finds the file hash in Redis, it immediately returns the cached JSON data to the `API Handler`, which then returns it to the client. The OCR and AI services are not called.
-   **Error Handling:** If at any point a component encounters a critical error (e.g., the AI Service receives an error from the Gemini API), it will propagate the error up to the `API Handler`, which will format and return a standardized JSON error response to the `n8n Workflow` with an appropriate HTTP status code (e.g., 400 or 500).

---
