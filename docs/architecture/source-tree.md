# 10. Source Tree

This proposed source tree is a refinement of the structure in the PRD. It incorporates our decision to use Poetry for dependency management and introduces an `api` sub-package to better organize the API routes, which is a common practice in larger FastAPI applications.

```plaintext
invoice-ocr-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app creation and router inclusion
│   ├── config.py               # Pydantic settings for configuration
│   ├── schemas.py              # Pydantic models for data validation
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints.py      # /extract and /health endpoint logic
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cache_service.py    # Redis cache logic
│   │   ├── ocr_service.py      # Surya-OCR logic
│   │   └── ai_service.py       # Gemini API logic
│   │
│   └── prompts/
│       ├── __init__.py
│       └── invoice_prompts.py    # Prompt templates for the AI service
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   └── test_services.py
│
├── .env.example                # Example environment variables
├── .gitignore
├── Dockerfile                  # Multi-stage Docker build file
├── docker-compose.yml          # Docker-compose for local development
├── pyproject.toml              # Poetry dependency management
└── README.md
```

---
