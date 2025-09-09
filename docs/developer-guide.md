# Developer Guide

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Testing Guide](#testing-guide)
5. [Code Quality](#code-quality)
6. [Debugging](#debugging)
7. [Performance Profiling](#performance-profiling)
8. [Contributing Guidelines](#contributing-guidelines)

---

## Development Environment Setup

### Prerequisites

#### Required Tools
- **Python 3.11.9+** - Main runtime
- **Poetry 1.4+** - Dependency management
- **Docker & Docker Compose** - Containerization
- **Git** - Version control
- **IDE/Editor** - VS Code, PyCharm, or similar

#### Optional Tools
- **Redis CLI** - For cache debugging
- **HTTPie or Postman** - API testing
- **jq** - JSON processing in scripts

### Initial Setup

#### 1. Clone Repository
```bash
git clone <repository-url>
cd supplier-invoice-automation
```

#### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
cat > .env << EOF
GOOGLE_API_KEY=your_google_gemini_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
LOG_LEVEL=INFO
EOF
```

#### 3. Python Environment Setup
```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate virtual environment
poetry shell
```

#### 4. Dependencies Installation
```bash
# Install all dependencies including dev dependencies
poetry install --no-root

# Install pre-commit hooks (optional)
poetry run pre-commit install
```

#### 5. Start Required Services
```bash
# Start Redis in background
docker run -d --name dev-redis -p 6379:6379 redis:7.2-alpine

# Verify Redis is running
redis-cli ping
# Expected output: PONG
```

#### 6. Verify Setup
```bash
# Run health check
poetry run uvicorn app.main:app --reload &
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Stop the server
pkill -f uvicorn
```

### IDE Configuration

#### VS Code Setup
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

#### PyCharm Configuration
1. Open project in PyCharm
2. Go to Settings → Project → Python Interpreter
3. Select "Poetry Environment" and point to project directory
4. Configure code style to use Black formatter
5. Enable type checking with mypy

---

## Project Structure

### Core Application Structure
```
app/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application and middleware
├── config.py                # Configuration management
├── schemas.py               # Pydantic data models
├── exceptions.py            # Custom exception hierarchy
├── utils.py                 # Utility functions
│
├── api/                     # API layer
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       └── endpoints.py     # REST API endpoints
│
├── services/                # Business logic layer
│   ├── __init__.py
│   ├── ai_service.py        # AI/ML service with circuit breaker
│   ├── ocr_service.py       # OCR text extraction
│   └── cache_service.py     # Redis caching service
│
└── prompts/                 # AI prompt templates
    ├── __init__.py
    └── invoice_prompts.py   # Structured extraction prompts
```

### Testing Structure
```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_api.py              # API integration tests
├── test_services.py         # Service unit tests
└── test_error_handling.py   # Error handling tests
```

### Documentation Structure
```
docs/
├── api-reference.md         # Complete API documentation
├── developer-guide.md       # This guide
├── architecture.md          # System architecture
├── deployment-guide.md      # Deployment instructions
├── stories/                 # Development stories
│   ├── 1.1.docker-fastapi-setup.story.md
│   ├── 1.3.redis-cache-setup.story.md
│   ├── 2.1.ai-service-integration.story.md
│   └── 3.1.error-handling.story.md
└── qa/gates/                # Quality assurance gates
    ├── 1.1-docker-fastapi-setup.yml
    ├── 1.3-redis-cache-setup.yml
    ├── 2.1-ai-service-integration.yml
    └── 3.1-error-handling.yml
```

---

## Development Workflow

### Daily Development Process

#### 1. Start Development Session
```bash
# Pull latest changes
git pull origin main

# Activate virtual environment
poetry shell

# Start Redis if not running
docker start dev-redis

# Start development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Feature Development
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test frequently
poetry run pytest -v

# Run code quality checks
poetry run black app tests
poetry run isort app tests
poetry run mypy app
poetry run flake8 app tests
```

#### 3. Testing During Development
```bash
# Run specific tests during development
poetry run pytest tests/test_services.py::TestAIService -v

# Run tests with coverage
poetry run pytest --cov=app --cov-report=term-missing

# Run integration tests
poetry run pytest tests/test_api.py -v

# Test error scenarios
poetry run pytest tests/test_error_handling.py -v
```

#### 4. Manual Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test file upload with sample invoice
curl -X POST http://localhost:8000/extract \
  -F "file=@sample_invoice.pdf" \
  | jq '.'

# Test error handling
curl -X POST http://localhost:8000/extract \
  -F "file=@invalid.txt"
```

### Environment Management

#### Development Environment Variables
```bash
# Core settings
export GOOGLE_API_KEY="your_development_api_key"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export LOG_LEVEL="DEBUG"

# Optional development settings
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PYTHONDONTWRITEBYTECODE=1
```

#### Environment Files
- `.env` - Local development (not in git)
- `.env.example` - Template (in git)
- `.env.test` - Test environment settings
- `.env.production` - Production settings template

---

## Testing Guide

### Test Categories

#### 1. Unit Tests
Test individual components in isolation:

```bash
# Service layer tests
poetry run pytest tests/test_services.py::TestAIService -v
poetry run pytest tests/test_services.py::TestOCRService -v
poetry run pytest tests/test_services.py::TestPromptManager -v

# Utility tests
poetry run pytest tests/test_utils.py -v
```

#### 2. Integration Tests
Test API endpoints and service interactions:

```bash
# API integration tests
poetry run pytest tests/test_api.py -v

# Full extraction workflow
poetry run pytest tests/test_api.py::TestExtractEndpoint::test_extract_endpoint_success_pdf -v
```

#### 3. Error Handling Tests
Test fault tolerance and error scenarios:

```bash
# Circuit breaker tests
poetry run pytest tests/test_error_handling.py::TestCircuitBreaker -v

# Exception handling tests
poetry run pytest tests/test_error_handling.py::TestExceptionMiddleware -v

# AI service error handling
poetry run pytest tests/test_error_handling.py::TestAIServiceErrorHandling -v
```

### Test Data Management

#### Creating Test Files
```bash
# Create test invoice files
mkdir -p tests/fixtures

# Small PDF for testing
echo '%PDF-1.4 test content' > tests/fixtures/sample.pdf

# Create invalid file for error testing
echo 'plain text content' > tests/fixtures/invalid.txt
```

#### Mock Configuration
Key mocking patterns used in tests:

```python
# Mock AI service responses
@patch('app.services.ai_service.genai')
def test_ai_service(self, mock_genai):
    mock_response = MagicMock()
    mock_response.text = '{"invoice_number": "INV-123"}'
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response

# Mock Redis for cache tests
@patch('app.services.cache_service.redis')
def test_cache_service(self, mock_redis):
    mock_redis.Redis.return_value.get.return_value = None
```

### Running Tests

#### Basic Test Execution
```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_api.py

# Run specific test class
poetry run pytest tests/test_services.py::TestAIService

# Run specific test method
poetry run pytest tests/test_api.py::TestExtractEndpoint::test_extract_endpoint_success_pdf
```

#### Advanced Test Options
```bash
# Run tests with coverage reporting
poetry run pytest --cov=app --cov-report=html --cov-report=term

# Run tests in parallel (if pytest-xdist installed)
poetry run pytest -n auto

# Run tests with detailed failure output
poetry run pytest --tb=long

# Run only failed tests from last run
poetry run pytest --lf

# Run tests matching pattern
poetry run pytest -k "test_ai_service or test_circuit_breaker"
```

#### Test Performance
```bash
# Run tests with duration reporting
poetry run pytest --durations=10

# Profile slow tests
poetry run pytest --profile

# Memory profiling (if pytest-memprof installed)
poetry run pytest --memprof
```

---

## Code Quality

### Formatting and Linting

#### Code Formatting (Black)
```bash
# Format all code
poetry run black app tests

# Check what would be formatted
poetry run black --check app tests

# Format specific file
poetry run black app/services/ai_service.py
```

#### Import Sorting (isort)
```bash
# Sort all imports
poetry run isort app tests

# Check import sorting
poetry run isort --check app tests

# Sort specific file
poetry run isort app/services/ai_service.py
```

#### Type Checking (mypy)
```bash
# Type check all code
poetry run mypy app

# Type check specific module
poetry run mypy app/services/ai_service.py

# Type check with detailed output
poetry run mypy --show-error-codes app
```

#### Linting (flake8)
```bash
# Lint all code
poetry run flake8 app tests

# Lint specific file
poetry run flake8 app/services/ai_service.py

# Show statistics
poetry run flake8 --statistics app tests
```

### Quality Automation

#### Pre-commit Hooks
```bash
# Install pre-commit
poetry run pre-commit install

# Run all hooks manually
poetry run pre-commit run --all-files

# Update hook versions
poetry run pre-commit autoupdate
```

#### Quality Check Script
Create `scripts/quality-check.sh`:
```bash
#!/bin/bash
set -e

echo "Running code quality checks..."

echo "1. Code formatting..."
poetry run black --check app tests

echo "2. Import sorting..."
poetry run isort --check app tests

echo "3. Type checking..."
poetry run mypy app

echo "4. Linting..."
poetry run flake8 app tests

echo "5. Running tests..."
poetry run pytest

echo "All quality checks passed!"
```

---

## Debugging

### Local Debugging

#### Debug Server Setup
```python
# app/main.py - Add debug configuration
import os
if os.getenv('DEBUG', 'false').lower() == 'true':
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("Waiting for debugger attach...")
    debugpy.wait_for_client()
```

#### VS Code Debug Configuration
Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/.venv/bin/uvicorn",
            "args": ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env"
        },
        {
            "name": "Python: Pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["${workspaceFolder}/tests/", "-v"],
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env"
        }
    ]
}
```

### Logging and Tracing

#### Debug Logging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
poetry run uvicorn app.main:app --reload

# Or in code
import logging
logging.getLogger("app").setLevel(logging.DEBUG)
```

#### Request Tracing
Every request gets a unique ID for tracing:
```bash
# Check request ID in logs
curl -v http://localhost:8000/health
# Look for X-Request-ID header in response
```

#### Service-Specific Debugging
```python
# AI Service debugging
from loguru import logger

# Add detailed logging in AI service
logger.debug(f"AI request prompt: {prompt[:100]}...")
logger.debug(f"AI response: {response.text[:200]}...")

# Circuit breaker state logging
logger.info(f"Circuit breaker state: {self.circuit_breaker.state}")
```

### Common Debugging Scenarios

#### 1. OCR Issues
```bash
# Test OCR with debug output
export LOG_LEVEL=DEBUG
python -c "
from app.services.ocr_service import OCRService
import asyncio

async def test_ocr():
    service = OCRService()
    result = await service.extract_text('sample.pdf')
    print(f'OCR Result: {result}')

asyncio.run(test_ocr())
"
```

#### 2. AI Service Issues
```bash
# Test AI service directly
python -c "
from app.services.ai_service import AIService
import asyncio
import os
os.environ['GOOGLE_API_KEY'] = 'your_key'

async def test_ai():
    service = AIService()
    result = await service.get_structured_data('Invoice #12345 Total: $100')
    print(f'AI Result: {result}')

asyncio.run(test_ai())
"
```

#### 3. Cache Issues
```bash
# Check Redis connection
redis-cli ping

# Monitor Redis operations
redis-cli monitor

# Check cache contents
redis-cli keys "*"
redis-cli get "cache_key_here"
```

#### 4. Circuit Breaker Issues
```python
# Monitor circuit breaker state
from app.services.ai_service import get_ai_service

service = get_ai_service()
print(f"Circuit breaker state: {service.circuit_breaker.state}")
print(f"Failure count: {service.circuit_breaker.failure_count}")
```

---

## Performance Profiling

### Application Profiling

#### Memory Profiling
```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler app/services/ai_service.py
```

#### Performance Testing
```bash
# Install load testing tools
pip install locust

# Create load test
cat > locustfile.py << EOF
from locust import HttpUser, task, between

class InvoiceUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health_check(self):
        self.client.get("/health")
    
    @task(3)
    def extract_invoice(self):
        with open("sample.pdf", "rb") as f:
            self.client.post("/extract", files={"file": f})
EOF

# Run load test
locust --host=http://localhost:8000
```

#### Database Performance
```bash
# Monitor Redis performance
redis-cli --latency-history -i 1

# Redis statistics
redis-cli info stats
```

### Profiling Tools Integration

#### cProfile Integration
```python
# Add profiling to specific functions
import cProfile
import pstats

def profile_function(func):
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
        
        return result
    return wrapper

# Use decorator on expensive functions
@profile_function
def expensive_function():
    pass
```

---

## Contributing Guidelines

### Code Standards

#### Python Code Style
- **Formatting**: Black (line length 88)
- **Import sorting**: isort with Black profile
- **Type hints**: Required for public APIs
- **Docstrings**: Google style
- **Variable naming**: snake_case
- **Constants**: UPPER_CASE

#### Example Code Pattern
```python
"""Module docstring describing purpose."""

from typing import Optional, Dict, Any
from loguru import logger

from app.exceptions import CustomError


class ExampleService:
    """Service class docstring.
    
    This class provides functionality for...
    
    Args:
        config: Configuration object
        
    Attributes:
        _client: Internal client instance
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._client: Optional[Any] = None
    
    async def process_data(self, input_data: str) -> Dict[str, Any]:
        """Process input data and return structured result.
        
        Args:
            input_data: Raw input to process
            
        Returns:
            Dictionary containing processed results
            
        Raises:
            CustomError: If processing fails
        """
        if not input_data.strip():
            raise CustomError("Input data cannot be empty")
        
        try:
            result = await self._internal_process(input_data)
            logger.info(f"Successfully processed data: {len(result)} items")
            return result
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise CustomError(f"Failed to process data: {e}")
    
    async def _internal_process(self, data: str) -> Dict[str, Any]:
        """Internal processing method."""
        # Implementation here
        return {"processed": True}
```

### Git Workflow

#### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

#### Commit Messages
Follow conventional commits format:
```
type(scope): brief description

Longer description if needed

Fixes #issue_number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

#### Pull Request Process
1. Create feature branch from `main`
2. Make changes with tests
3. Run quality checks locally
4. Push branch and create PR
5. Address review feedback
6. Merge after approval

### Testing Requirements

#### Minimum Test Coverage
- **Overall**: 90%+ line coverage
- **New features**: 95%+ line coverage
- **Critical paths**: 100% branch coverage
- **Error handling**: All error scenarios tested

#### Required Tests
- Unit tests for all public methods
- Integration tests for API endpoints
- Error handling tests for all failure modes
- Performance tests for critical paths

#### Test Documentation
```python
def test_example_service_success():
    """Test successful data processing.
    
    This test verifies that the service correctly processes
    valid input data and returns expected results.
    """
    # Arrange
    service = ExampleService({"key": "value"})
    input_data = "test data"
    
    # Act
    result = await service.process_data(input_data)
    
    # Assert
    assert result["processed"] is True
    assert "data" in result
```

### Documentation Requirements

#### Code Documentation
- Module docstrings for all modules
- Class docstrings with purpose and usage
- Method docstrings with args, returns, raises
- Inline comments for complex logic

#### API Documentation
- OpenAPI/Swagger spec must be complete
- All endpoints documented with examples
- Error responses documented
- Schema definitions complete

#### Architecture Documentation
- High-level architecture diagrams
- Service interaction diagrams
- Database/cache relationships
- External API integrations

---

## Development Tips

### Performance Optimization
1. **Use async/await** for I/O operations
2. **Cache expensive operations** with Redis
3. **Implement circuit breakers** for external services
4. **Monitor memory usage** in loops
5. **Profile before optimizing** to find bottlenecks

### Error Handling Best Practices
1. **Use custom exceptions** with proper status codes
2. **Log errors with context** (request ID, user info)
3. **Implement retry logic** for transient failures
4. **Validate input early** to fail fast
5. **Provide actionable error messages** to users

### Security Considerations
1. **Validate all input** including file types and sizes
2. **Sanitize error messages** to avoid information leakage
3. **Use environment variables** for secrets
4. **Implement rate limiting** in production
5. **Monitor for unusual patterns** in logs

### Debugging Tips
1. **Use structured logging** with consistent formats
2. **Include request IDs** in all log messages
3. **Test error scenarios** during development
4. **Use debugger** instead of print statements
5. **Monitor external service health** proactively

---

For additional help or questions, refer to the project documentation or contact the development team.