# 2. High Level Architecture

## 2.1. Technical Summary

The system is designed as a standalone, containerized microservice following a RESTful architecture. The core components include a FastAPI web server providing the main API, a dedicated OCR service utilizing Surya-OCR for text and table extraction, an AI service for structured data extraction via the Gemini API, and a Redis cache to store results of previously processed invoices. This architecture directly supports the PRD's goals of creating an independent, high-performance, and cost-effective invoice processing service.

## 2.2. High Level Overview

The primary architectural style is a **Microservice**, as this application is a self-contained service responsible for a single business capability (invoice data extraction). It will be managed in its own repository (**Polyrepo** model), as implied by the PRD's repository structure.

The data flow is as follows:
1.  The `n8n` workflow sends a `POST` request with a file (PDF/image) to the `/extract` endpoint.
2.  The service calculates a hash of the file and checks the Redis cache. If a result exists, it is returned immediately.
3.  If not in the cache, the file is passed to the **Surya-OCR Service** for text, line, and table detection.
4.  The extracted text and table data are passed to the **AI Service**, which uses a structured prompt to call the Gemini API.
5.  The resulting JSON from the AI is normalized (e.g., date formats, number conversion).
6.  The final, structured JSON data is stored in the Redis cache and returned to the `n8n` workflow.

## 2.3. High Level Project Diagram

```mermaid
graph TD
    subgraph "Invoice OCR Service (Docker)"
        direction LR
        A[FastAPI Endpoint /extract] --> B{Cache Check};
        B -- "Cache Miss" --> C[OCR Service (Surya)];
        C --> D[AI Service (Gemini)];
        D --> E[Data Normalization];
        E --> F[Store in Cache];
        F --> G[JSON Response];
        B -- "Cache Hit" --> G;
    end

    subgraph "External Systems"
        N8N([n8n Workflow]);
        R([Redis Cache]);
        AI_API([Google Gemini API]);
    end

    N8N -- "POST PDF/Image" --> A;
    A --> R;
    C --> AI_API;
    F -.-> R;
    G -- "Success/Error" --> N8N;

    style A fill:#90EE90
```

## 2.4. Architectural and Design Patterns

- **Microservice Architecture:** The service is designed as a single, independently deployable unit focused exclusively on invoice processing.
    - _Rationale:_ This decouples the complex OCR/AI logic from the main n8n orchestration, allowing it to be scaled, updated, and maintained separately.
- **REST API:** The service exposes its functionality via a simple, stateless HTTP interface.
    - _Rationale:_ This is a universally understood standard that ensures easy integration with clients like n8n and simplifies testing.
- **Repository Pattern:** The application logic will interact with external services (OCR, AI, Cache) through dedicated service modules/repositories.
    - _Rationale:_ This decouples the core business logic from the specific implementation of external tools. For example, we can easily swap out `Gemini` for `Claude` in the `AIService` without changing the main application flow.
- **Cache-Aside Strategy:** The application code is responsible for checking the cache for an existing result before executing the expensive OCR and AI processing steps.
    - _Rationale:_ This is explicitly required by the PRD (FR6) to reduce latency and API costs for repeated processing of the same invoice.

---
