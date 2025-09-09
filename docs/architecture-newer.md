# System Architecture

## Overview

The Supplier Invoice Automation Service is a microservice-based application designed to extract structured data from invoice files using OCR and AI technologies. The system follows modern architectural patterns including circuit breaker, retry logic, caching, and comprehensive error handling.

### Key Architectural Principles

- **Separation of Concerns**: Clear boundaries between API, business logic, and data layers
- **Fault Tolerance**: Circuit breaker pattern and retry logic for external dependencies
- **Performance**: Intelligent caching and connection pooling
- **Observability**: Comprehensive logging and request tracing
- **Testability**: Dependency injection and comprehensive test coverage

### System Qualities

- **Reliability**: 99.9% uptime target with graceful degradation
- **Performance**: Sub-5-second response time for invoice processing
- **Scalability**: Horizontal scaling capability with stateless design
- **Security**: Input validation, error sanitization, audit trails
- **Maintainability**: Clean code architecture with comprehensive testing

## System Components

The application consists of several key components working together to process invoice files and extract structured data.

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **FastAPI Application** | HTTP request handling, routing, middleware | FastAPI, Uvicorn |
| **AI Service** | AI interaction, circuit breaker, retry logic | Google Gemini API |
| **OCR Service** | Text extraction from documents | Surya OCR |
| **Cache Service** | Result caching and retrieval | Redis |
| **Circuit Breaker** | Fault tolerance and failure isolation | Custom implementation |
| **Request Tracking** | Correlation ID management | UUID generation |
| **Structured Logging** | Comprehensive operation logging | Loguru |

## Service Architecture

### Layered Architecture

The application follows a clean layered architecture pattern:

#### 1. API Layer (`app/api/`)
**Responsibilities:**
- HTTP request/response handling
- Input validation and sanitization
- Error response formatting
- Request correlation tracking

**Key Components:**
- `endpoints.py` - REST API endpoints
- Request/response models
- FastAPI dependency injection

#### 2. Business Logic Layer (`app/services/`)
**Responsibilities:**
- Core business logic implementation
- External service integration
- Data transformation and validation
- Error handling and recovery

**Key Components:**
- `ai_service.py` - AI processing with fault tolerance
- `ocr_service.py` - Document text extraction
- `cache_service.py` - Result caching and retrieval

#### 3. Infrastructure Layer
**Responsibilities:**
- External service clients
- Configuration management
- Logging and monitoring
- Resource management

**Key Components:**
- Redis connection management
- Google Gemini API client
- Structured logging configuration

## Data Models

### Core Data Structures

#### InvoiceData (Pydantic Model)
```python
class InvoiceData(BaseModel):
    invoice_number: str                    # Required invoice identifier
    invoice_date: Optional[date] = None    # Invoice issue date
    due_date: Optional[date] = None        # Payment due date
    vendor_name: str                       # Vendor/supplier name
    vendor_address: Optional[str] = None   # Vendor address
    customer_name: Optional[str] = None    # Customer/buyer name
    customer_address: Optional[str] = None # Customer address
    subtotal: float                        # Subtotal amount
    tax: float                             # Tax amount
    total: float                           # Total amount
    currency: str = "USD"                  # Currency code
    items: List[ExtractedItem] = []        # Line items
```

#### ExtractedItem (Pydantic Model)
```python
class ExtractedItem(BaseModel):
    description: str      # Item description
    quantity: float       # Item quantity
    unit_price: float     # Price per unit
    total_price: float    # Total price for item
```

### Data Validation Rules

#### File Validation
- **Supported formats**: PDF, PNG, JPG, JPEG
- **Maximum size**: 10MB (10,485,760 bytes)
- **Content type validation**: MIME type checking
- **File structure validation**: Basic format verification

#### Data Extraction Validation
- **Required fields**: invoice_number, vendor_name, subtotal, tax, total
- **Optional fields**: All date and address fields
- **Numeric validation**: subtotal, tax, total must be valid numbers
- **Date validation**: ISO format (YYYY-MM-DD) when present
- **Currency validation**: Valid currency codes (default USD)

## External Integrations

### Google Gemini AI Integration

#### Configuration
```python
# API Configuration
GEMINI_MODEL = "gemini-2.5-pro"
API_KEY_SOURCE = "environment_variable"  # GOOGLE_API_KEY
TIMEOUT = 30  # seconds
```

#### Error Handling
- **Transient errors**: 429, 500, 502, 503, 504, timeouts
- **Permanent errors**: 400, 401, 403, invalid API key
- **Retry strategy**: 3 attempts with exponential backoff
- **Circuit breaker**: 5 failure threshold, 60-second timeout

### Redis Cache Integration

#### Configuration
```python
# Connection Configuration
REDIS_HOST = "redis"  # Docker service name
REDIS_PORT = 6379
REDIS_DB = 0
CONNECTION_POOL_SIZE = 10
SOCKET_TIMEOUT = 5  # seconds
```

#### Connection Management
- **Connection pooling**: Efficient resource usage
- **Automatic reconnection**: Handle network interruptions
- **Graceful degradation**: Service continues without cache
- **Error logging**: Cache failures don't block processing

### Surya OCR Integration

#### Processing Pipeline
1. **File validation**: Format and size checking
2. **Format handling**: PDF → images, images → direct processing
3. **Text extraction**: Surya OCR processing
4. **Text cleanup**: Post-processing and formatting
5. **Error handling**: Graceful failure with detailed logging

## Error Handling Strategy

### Exception Hierarchy

The application uses a comprehensive custom exception hierarchy:

| Exception | HTTP Status | Use Case | Retry |
|-----------|-------------|----------|-------|
| `InvalidFileTypeError` | 400 | Unsupported file format | No |
| `FileProcessingError` | 400 | File too large, corrupted | No |
| `OcrError` | 500 | OCR processing failure | No |
| `AiServiceError` | 500 | AI processing failure | Depends |
| `CircuitBreakerOpenError` | 503 | Circuit breaker open | Yes |
| `CacheError` | 500 | Cache operation failure | No |

### Error Response Format

All errors follow a standardized format:
```json
{
    "error": "Human-readable error message",
    "detail": "Additional technical details (optional)"
}
```

## Caching Strategy

### Cache Key Strategy
```python
# Key Generation
def generate_cache_key(file_content: bytes) -> str:
    file_hash = hashlib.sha256(file_content).hexdigest()
    return f"invoice_cache:{file_hash}"

# Benefits:
# - Identical files return same key
# - Content-based, not filename-based
# - Cryptographically secure hash
# - Deterministic across requests
```

### Cache Policies

#### Time-to-Live (TTL)
- **Duration**: 24 hours (86400 seconds)
- **Rationale**: Balance between performance and data freshness
- **Automatic cleanup**: Redis handles expiration

## Security Architecture

### Security Controls

#### Input Validation
- **File type checking**: MIME type and extension validation
- **File size limits**: 10MB maximum to prevent DoS
- **Content validation**: Basic file structure verification
- **Path sanitization**: Prevent directory traversal attacks

#### Data Protection
- **No persistent storage**: Files processed in memory/temp directories
- **Automatic cleanup**: Temporary files deleted after processing
- **Error sanitization**: No sensitive data in error messages
- **Audit logging**: All operations logged with request IDs

#### Infrastructure Security
- **Secret management**: Environment variables for API keys
- **Container security**: Non-root user, minimal image
- **Network security**: Service isolation, minimal exposed ports
- **Dependency scanning**: Regular vulnerability assessments

## Performance Considerations

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Response Time** | <5s (95th percentile) | End-to-end processing |
| **Throughput** | 100 requests/hour | Sustained load |
| **Cache Hit Rate** | >70% | Identical file processing |
| **Memory Usage** | <512MB per instance | Peak memory consumption |
| **CPU Usage** | <80% average | Under normal load |

### Performance Optimization Strategies

#### Caching Optimizations
- **File-based caching**: Identical files return immediately
- **Connection pooling**: Efficient Redis connections
- **Lazy loading**: Services initialized on first use
- **Memory management**: Efficient object lifecycle

#### Processing Optimizations
- **Async/await**: Non-blocking I/O operations
- **Circuit breaker**: Prevent resource waste during failures
- **Retry with backoff**: Intelligent failure handling
- **Streaming**: Large file processing optimizations

## Monitoring and Observability

### Logging Strategy

#### Structured Logging Format
```json
{
    "timestamp": "2024-01-15T10:30:00.000Z",
    "level": "INFO",
    "message": "Invoice processing completed",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_agent": "curl/7.68.0",
    "processing_time_ms": 2340,
    "file_size_bytes": 234567,
    "cache_hit": false,
    "ai_model_used": "gemini-2.5-pro",
    "extraction_success": true
}
```

### Metrics Collection

#### Application Metrics
- **Request rate**: Requests per second
- **Response time**: Percentiles (50th, 95th, 99th)
- **Error rate**: Error percentage by type
- **Cache hit rate**: Cache effectiveness
- **Circuit breaker state**: Service health

### Health Checks

#### Application Health
```json
GET /health
{
    "status": "ok",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "version": "1.0.0",
    "checks": {
        "redis": "ok",
        "ai_service": "ok",
        "ocr_service": "ok"
    }
}
```

## Deployment Architecture

### Container Configuration

#### Multi-stage Dockerfile
```dockerfile
# Build stage
FROM python:3.11.9-slim as builder
# Install dependencies and build application

# Runtime stage  
FROM python:3.11.9-slim as runtime
# Copy built application and run as non-root user
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration

#### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_api_key_here
REDIS_HOST=redis_hostname
REDIS_PORT=6379

# Optional
LOG_LEVEL=INFO
REDIS_DB=0
REDIS_PASSWORD=optional_password
MAX_FILE_SIZE=10485760
CIRCUIT_BREAKER_TIMEOUT=60
```

## Future Architectural Considerations

### Planned Enhancements

1. **Authentication & Authorization**
   - API key-based authentication
   - Role-based access control
   - Request rate limiting per user

2. **Advanced Caching**
   - Multi-level caching strategy
   - Cache warming mechanisms
   - Intelligent cache invalidation

3. **Multi-AI Provider Support**
   - Plugin architecture for AI providers
   - Automatic failover between providers
   - Cost optimization routing

4. **Advanced Monitoring**
   - Distributed tracing
   - Real-time alerting
   - Performance analytics dashboard

### Scalability Roadmap

- **Phase 1**: Single instance deployment (current)
- **Phase 2**: Horizontal scaling with load balancer
- **Phase 3**: Microservices decomposition
- **Phase 4**: Event-driven architecture
- **Phase 5**: Multi-region deployment

---

This architecture documentation provides a comprehensive view of the current system design and serves as a foundation for future enhancements and scaling decisions.