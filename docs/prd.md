# PRD: Invoice OCR & AI Extraction Service

## Goals and Background Context

### Goals
- Vytvořit samostatnou mikroslužbu pro OCR a AI extrakci faktur
- Služba bude volána z n8n přes HTTP endpoint
- Minimalizovat náklady používáním cache a efektivních AI promptů
- Dosáhnout >95% přesnosti extrakce klíčových polí

### Background Context
N8n orchestrace již běží na serveru. Potřebujeme doplnit chybějící OCR/AI komponentu, která bude zpracovávat PDF faktury a vracet strukturovaná data pro import do EspoCRM.

## Requirements

### Functional Requirements
- **FR1**: HTTP endpoint přijímající soubor faktury (PDF, PNG, JPG) (POST /extract)
- **FR2**: OCR zpracování pomocí Surya-OCR s podporou češtiny
- **FR3**: Detekce a extrakce tabulek s položkami faktury
- **FR4**: AI extrakce strukturovaných dat (Gemini/OpenAI/Claude API)
- **FR5**: Vrácení JSON odpovědi s extrahovanými daty
- **FR6**: Redis cache pro již zpracované faktury (hash-based)
- **FR7**: Confidence scoring pro každé extrahované pole
- **FR8**: Možnost označení faktur s nízkým confidence score (<95%) pro manuální kontrolu v EspoCRM.
- **FR9**: Vracení specifických chybových kódů pro scénáře selhání (např. `UNSUPPORTED_FILE_TYPE`, `FILE_PASSWORD_PROTECTED`, `NOT_AN_INVOICE`), aby je bylo možné zpracovat v n8n.

### Non-Functional Requirements
- **NFR1**: Zpracování jedné faktury < 30 sekund
- **NFR2**: Služba běží jako Docker container
- **NFR3**: Health check endpoint (GET /health)
- **NFR4**: Strukturované logování pro debugging
- **NFR5**: Graceful error handling s informativními chybami
- **NFR6**: Podpora souběžného zpracování (2-4 workers)

## Technical Assumptions

### Stack
- **Language**: Python 3.11
- **Framework**: FastAPI (async support)
- **OCR**: Surya-OCR
- **AI Provider**: Gemini (primary), OpenAI/Claude (fallback)
- **Cache**: Redis
- **Container**: Docker s multi-stage build
- **Deployment**: Docker container na Hetzner serveru

### Repository Structure
```
invoice-ocr-service/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py           # FastAPI app
│   ├── config.py         # Configuration
│   ├── models.py         # Pydantic models
│   ├── services/
│   │   ├── ocr.py       # Surya-OCR service
│   │   ├── ai.py        # AI extraction
│   │   └── cache.py     # Redis operations
│   └── prompts/
│       └── invoice_cz.py # Czech invoice prompt
```

## Epic Structure

### Epic 1: Service Foundation
**Goal**: Základní služba s OCR a health check

**Story 1.1: Docker & FastAPI Setup**
- Vytvoření Dockerfile s Surya-OCR dependencies
- FastAPI aplikace s health endpoint
- Docker-compose konfigurace
- AC: Service běží, /health vrací 200

**Story 1.2: Surya-OCR Integration**
- Implementace OCR service
- Endpoint /extract přijímající PDF
- Vrácení plain textu
- AC: PDF → text konverze funguje

**Story 1.3: Redis Cache Setup**
- Redis container v docker-compose
- Cache service s hash-based storage
- TTL 24 hodin
- AC: Opakované requesty vrací cached response

### Epic 2: AI Data Extraction
**Goal**: Strukturovaná extrakce dat z OCR textu

**Story 2.1: AI Service Integration**
- Gemini API client
- Fallback na OpenAI/Claude
- Strukturovaný prompt pro faktury
- AC: Text → JSON extrakce funguje

**Story 2.2: Table Detection**
- Surya table detection
- Extrakce položek faktury
- Mapování sloupců tabulky
- AC: Položky faktury správně extrahovány

**Story 2.3: Data Normalization**
- Normalizace datumů na ISO formát
- Převod čísel na float
- Čištění whitespace
- AC: Data v konzistentním formátu

### Epic 3: Production Readiness
**Goal**: Služba připravená pro produkci

**Story 3.1: Error Handling**
- Graceful error responses
- Retry logic pro AI API
- Circuit breaker pattern
- AC: Service se nezhroutí při chybách

**Story 3.2: Monitoring & Logging**
- Strukturované JSON logy
- Request ID tracking
- Performance metrics
- AC: Logy umožňují debugging

**Story 3.3: Configuration & Security**
- Environment variables
- API key management
- Rate limiting
- AC: Secrets nejsou v kódu

**Story 3.4: Secure API Endpoint**
- Implement API key authentication on the /extract endpoint.
- Reject requests without a valid API key.
- AC: Endpoint is protected and only accessible by authorized clients (n8n).

**Story 3.5: Implement CI/CD Pipeline**
- Create a GitHub Actions workflow for automated testing and deployment.
- The pipeline should build the Docker image and push it to a registry.
- The pipeline should deploy the new image to the Hetzner server.
- AC: Pushing to the main branch automatically deploys the service to production.

## API Specification

### POST /extract
```json
Request:
  Content-Type: multipart/form-data
  Body: file (PDF)

Response 200:
{
  "success": true,
  "confidence": 0.92,
  "cached": false,
  "data": {
    "supplier": {
      "name": "Dodavatel s.r.o.",
      "ico": "12345678",
      "dic": "CZ12345678",
      "iban": "CZ6508000000192000145399"
    },
    "invoice": {
      "invoiceNumber": "2025-000123",
      "issueDate": "2025-01-01",
      "dueDate": "2025-01-14",
      "variableSymbol": "1234567890"
    },
    "totals": {
      "withoutTax": 10000.0,
      "tax": 2100.0,
      "withTax": 12100.0
    },
    "items": [
      {
        "name": "Služba A",
        "quantity": 1,
        "unitPrice": 10000.0,
        "vatRate": 21.0,
        "lineTotal": 12100.0
      }
    ]
  }
}

Response 400/500:
{
  "success": false,
  "error": "Error description",
  "requestId": "uuid"
}
```

## Success Metrics
- Extrakce přesnost > 95% pro klíčová pole
- Response time < 30s (P95)
- Cache hit rate > 30%
- Zero downtime deployments
- AI API costs < $0.05 per invoice5% pro klíčová pole
- Response time < 30s (P95)
- Cache hit rate > 30%
- Zero downtime deployments
- AI API costs < $0.05 per invoice < $0.05 per invoice